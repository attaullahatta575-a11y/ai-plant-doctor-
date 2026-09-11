"""Vision/AI service.

SRP: image validation, Groq vision request, and Pydantic validation.
No Streamlit UI and no database logic live here.
"""

from __future__ import annotations

import base64
import json
from io import BytesIO

from groq import Groq
from PIL import Image, UnidentifiedImageError

from config import Settings
from models import VisionAnalysis


SYSTEM_PROMPT = """
You are the vision engine for an AI Leaf Doctor.

The user uploads ONE close-up photograph of a plant leaf.

Your job:
1. Decide whether the image actually contains a clear plant leaf.
2. Identify the plant if reasonably possible.
3. Analyze visible leaf health problems.
4. Give cautious, practical first-aid guidance.

Important safety/accuracy rules:
- Do not invent certainty. Use lower confidence when the image is ambiguous.
- If the image is not a clear leaf, set image_is_leaf=false.
- If you cannot reliably identify the plant, use "Unknown" for names and a low confidence score.
- Do not claim an exact nutrient deficiency from a photo alone.
- Do not invent chemical pesticide/fungicide doses.
- Distinguish visual symptoms from confirmed diagnoses.
- Solutions must be general, low-risk plant-care guidance.
- Return ONLY JSON matching the requested schema.
"""


JSON_SCHEMA_DESCRIPTION = """
{
  "image_is_leaf": true,
  "image_quality": "good",
  "plant_local_name": "string",
  "plant_english_name": "string",
  "plant_botanical_name": "string",
  "identification_confidence": 0,
  "health_status": "healthy",
  "detected_issue": "string",
  "issue_type": "none",
  "severity": "none",
  "symptoms": ["string"],
  "possible_causes": ["string"],
  "ai_solution": ["string"],
  "health_confidence": 0,
  "notes": ["string"]
}
"""


def validate_image(image_bytes: bytes, max_image_mb: int) -> tuple[str, tuple[int, int]]:
    """Validate and normalize an uploaded image without making AI calls."""
    if not image_bytes:
        raise ValueError("The uploaded file is empty.")

    max_bytes = max_image_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise ValueError(f"Image is too large. Maximum allowed size is {max_image_mb} MB.")

    try:
        image = Image.open(BytesIO(image_bytes))
        image.verify()
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
        image_format = (image.format or "").lower()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    if width < 256 or height < 256:
        raise ValueError("Please upload a clearer leaf image of at least 256×256 pixels.")

    mime = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(image_format)

    if not mime:
        raise ValueError("Please use JPG, JPEG, PNG, or WEBP.")

    return mime, (width, height)


def _data_url(image_bytes: bytes, mime: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def analyze_leaf(image_bytes: bytes, settings: Settings) -> VisionAnalysis:
    """Send the image to Groq and validate the JSON response with Pydantic."""
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Create a .env file and add your Groq API key."
        )

    mime, dimensions = validate_image(image_bytes, settings.max_image_mb)
    image_url = _data_url(image_bytes, mime)

    user_prompt = f"""
Analyze this single leaf image.

Image dimensions: {dimensions[0]} x {dimensions[1]}.

Return ONLY a JSON object with exactly these fields and compatible values:

{JSON_SCHEMA_DESCRIPTION}

Field rules:
- image_quality must be one of: good, acceptable, poor
- health_status must be one of: healthy, possibly_unhealthy, uncertain
- issue_type must be one of: none, disease, pest, nutrient_like_symptom, physical_damage, uncertain
- severity must be one of: none, low, medium, high, uncertain
- identification_confidence and health_confidence are percentages from 0 to 100.
- symptoms, possible_causes, ai_solution, and notes are arrays of strings.
"""

    client = Groq(api_key=settings.groq_api_key)

    response = client.chat.completions.create(
        model=settings.vision_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                ],
            },
        ],
        temperature=0.2,
        max_completion_tokens=1600,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The AI returned an empty response.")

    try:
        payload = json.loads(content)
        return VisionAnalysis.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            "The AI returned data that did not match the Plant Doctor schema."
        ) from exc
