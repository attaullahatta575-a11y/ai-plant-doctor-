"""Care recommendation service.

SRP: converts AI diagnosis + trusted database information into
fertilizer and watering recommendations. It does not call Groq.
"""

from __future__ import annotations

from typing import Any

from models import FertilizerRecommendation, VisionAnalysis, WateringRecommendation


def build_fertilizer_recommendation(
    plant: dict[str, Any] | None,
    vision: VisionAnalysis,
) -> FertilizerRecommendation:
    """Build a database-driven fertilizer recommendation."""
    if not plant:
        return FertilizerRecommendation(
            available=False,
            recommendation=(
                "No matching plant-care record was found in the local database. "
                "Do not guess a fertilizer product from the image alone."
            ),
            fertilizer_type="Database entry unavailable",
            application_guidance="Use a locally appropriate product label or obtain expert advice.",
            precautions=[
                "Avoid applying fertilizer solely because a leaf looks unhealthy.",
                "A photo cannot confirm an exact nutrient deficiency.",
            ],
        )

    if vision.health_status == "uncertain":
        return FertilizerRecommendation(
            available=True,
            recommendation=(
                "Use the plant's normal fertilizer program only; the image is not "
                "clear enough to justify a condition-specific fertilizer change."
            ),
            fertilizer_type=plant["fertilizer_type"],
            application_guidance=plant["fertilizer_guidance"],
            precautions=[plant["fertilizer_precautions"]],
        )

    return FertilizerRecommendation(
        available=True,
        recommendation=(
            f"For {plant['english_name']}: {plant['fertilizer_type']}"
        ),
        fertilizer_type=plant["fertilizer_type"],
        application_guidance=plant["fertilizer_guidance"],
        precautions=[
            plant["fertilizer_precautions"],
            "The visual diagnosis does not prove a nutrient deficiency.",
        ],
    )


def build_watering_recommendation(
    plant: dict[str, Any] | None,
) -> WateringRecommendation:
    """Return database-driven general watering guidance."""
    if not plant:
        return WateringRecommendation(
            available=False,
            requirement="Unknown",
            frequency="No plant-specific record available.",
            guidance=[
                "Check soil moisture before watering.",
                "Avoid watering solely because the leaf appears unhealthy.",
            ],
        )

    return WateringRecommendation(
        available=True,
        requirement=plant["water_requirement"],
        frequency=plant["watering_frequency"],
        guidance=[plant["watering_guidance"]],
    )
