"""Application configuration.

Loads environment variables and exposes a small, typed configuration object.
Secrets are never hard-coded in this file.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    vision_model: str = "qwen/qwen3.8-27b"
    database_path: str = "database.bd"
    max_image_mb: int = 20


def get_settings() -> Settings:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    return Settings(
        groq_api_key=api_key,
        vision_model=os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b").strip(),
        database_path=os.getenv("DATABASE_PATH", "database.bd").strip(),
        max_image_mb=int(os.getenv("MAX_IMAGE_MB", "20")),
    )
