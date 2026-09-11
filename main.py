"""Streamlit entry point for AI Plant Doctor.

SRP: presentation/orchestration only. Business rules and AI calls live
in their own modules.
"""

from pathlib import Path
import importlib.util

import streamlit as st

from config import get_settings
from database import init_db, get_plant_by_botanical_name
from models import PlantDoctorReport

# Hyphenated module filename requested by the user.
_spec = importlib.util.spec_from_file_location(
    "vision_service",
    Path(__file__).with_name("vision-service.py"),
)
vision_service = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(vision_service)

_spec2 = importlib.util.spec_from_file_location(
    "care_service",
    Path(__file__).with_name("care-service.py"),
)
care_service = importlib.util.module_from_spec(_spec2)
assert _spec2.loader is not None
_spec2.loader.exec_module(care_service)


st.set_page_config(
    page_title="AI Plant Doctor",
    page_icon="🍃",
    layout="wide",
)

settings = get_settings()
init_db(settings.database_path)

st.title("🍃 AI Plant Doctor")
st.caption("Upload one clear leaf photo. The AI identifies the plant and analyzes visible health issues.")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        """
        1. Upload a clear leaf photo.
        2. AI identifies the plant.
        3. AI checks visible health problems.
        4. Local database provides care information.
        5. Python builds fertilizer and watering recommendations.
        """
    )
    st.info(
        "This is an AI-assisted plant-care tool, not a laboratory diagnosis. "
        "Use an expert or laboratory test for high-stakes crop decisions."
    )

uploaded_file = st.file_uploader(
    "Upload a leaf image",
    type=["jpg", "jpeg", "png", "webp"],
    help="Use a single, clear, close-up photo of one leaf.",
)

if uploaded_file is None:
    st.markdown("### Start here")
    st.write("Upload a clear leaf photo to receive a Plant Doctor report.")
    st.stop()

image_bytes = uploaded_file.getvalue()
st.image(image_bytes, caption="Uploaded leaf", width="stretch")

if st.button("🔎 Analyze Leaf", type="primary", use_container_width=True):
    try:
        with st.spinner("Analyzing the leaf..."):
            vision = vision_service.analyze_leaf(image_bytes, settings)

        if not vision.image_is_leaf:
            st.error(
                "The uploaded image does not look like a clear leaf. "
                "Please upload one close-up leaf photo."
            )
            st.stop()

        if vision.image_quality == "poor":
            st.warning(
                "The image quality is poor. Results may be unreliable. "
                "A clearer, closer leaf photo is recommended."
            )

        plant = get_plant_by_botanical_name(
            settings.database_path,
            vision.plant_botanical_name,
        )

        fertilizer = care_service.build_fertilizer_recommendation(plant, vision)
        watering = care_service.build_watering_recommendation(plant)

        report = PlantDoctorReport(
            vision=vision,
            fertilizer=fertilizer,
            watering=watering,
            database_match=plant is not None,
        )

        st.session_state["report"] = report
        st.session_state["uploaded_image"] = image_bytes

    except Exception as exc:
        st.error(f"Could not complete the analysis: {exc}")
        st.stop()


report = st.session_state.get("report")

if report:
    vision = report.vision

    st.divider()
    st.header("🩺 Plant Doctor Report")

    if report.database_match:
        st.success("Plant identified and matched with the local care database.")
    else:
        st.warning(
            "The plant was identified by AI, but no matching local database record "
            "was found. Fertilizer and watering advice is therefore limited."
        )

    st.subheader("🌿 Plant Identification")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("English Name", vision.plant_english_name)
    with col2:
        st.metric("Botanical Name", vision.plant_botanical_name)
    with col3:
        st.metric("Identification Confidence", f"{vision.identification_confidence:.0f}%")

    st.write(f"**Local Name:** {vision.plant_local_name}")
    st.write(f"**Image quality:** {vision.image_quality}")

    st.subheader("🦠 Health Analysis")
    h1, h2, h3 = st.columns(3)
    with h1:
        st.metric("Health", vision.health_status.replace("_", " ").title())
    with h2:
        st.metric("Issue", vision.detected_issue)
    with h3:
        st.metric("Severity", vision.severity.title())

    st.write(f"**Health confidence:** {vision.health_confidence:.0f}%")

    if vision.symptoms:
        st.markdown("**Visible symptoms**")
        for item in vision.symptoms:
            st.write(f"- {item}")

    if vision.possible_causes:
        st.markdown("**Possible causes**")
        for item in vision.possible_causes:
            st.write(f"- {item}")

    if vision.ai_solution:
        st.markdown("**AI first-aid guidance**")
        for item in vision.ai_solution:
            st.write(f"- {item}")

    st.subheader("🌱 Fertilizer")
    st.write(f"**Recommendation:** {report.fertilizer.recommendation}")
    st.write(f"**Type:** {report.fertilizer.fertilizer_type}")
    st.write(f"**Application:** {report.fertilizer.application_guidance}")
    for item in report.fertilizer.precautions:
        st.write(f"- ⚠️ {item}")

    st.subheader("💧 Watering")
    st.write(f"**Requirement:** {report.watering.requirement}")
    st.write(f"**Frequency:** {report.watering.frequency}")
    for item in report.watering.guidance:
        st.write(f"- {item}")

    if vision.notes:
        st.subheader("📝 Notes")
        for item in vision.notes:
            st.write(f"- {item}")

    st.download_button(
        "⬇️ Download structured JSON report",
        data=report.model_dump_json(indent=2),
        file_name="plant_doctor_report.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("View structured JSON"):
        st.json(report.model_dump())
