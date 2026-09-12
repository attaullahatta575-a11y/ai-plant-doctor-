import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    groq_api_key: str
    vision_model: str
    database_path: str
    max_image_mb: int


def get_secret(name: str, default: str = "") -> str:
    """
    Read a secret from Streamlit Cloud first.
    If Streamlit is not available, use environment variables.
    """

    # Streamlit Cloud
    try:
        import streamlit as st

        value = st.secrets.get(name)

        if value:
            return str(value)

    except Exception:
        pass

    # Local .env / environment variable
    return os.getenv(name, default)


def get_settings() -> Settings:
    groq_api_key = get_secret("GROQ_API_KEY")

    if not groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add GROQ_API_KEY in Streamlit Cloud Secrets."
        )

    return Settings(
        groq_api_key=groq_api_key,
        vision_model=get_secret(
            "GROQ_VISION_MODEL",
            "qwen/qwen3.8-27b"
        ),
        database_path=get_secret(
            "DATABASE_PATH",
            "database.bd"
        ),
        max_image_mb=int(
            get_secret(
                "MAX_IMAGE_MB",
                "20"
            )
        ),
    )
