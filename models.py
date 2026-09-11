"""Pydantic data models shared between services.

This file contains data contracts only. It does not call APIs or databases.
"""

from typing import Literal
from pydantic import BaseModel, Field


class VisionAnalysis(BaseModel):
    """Structured result returned by the vision model."""

    image_is_leaf: bool
    image_quality: Literal["good", "acceptable", "poor"]
    plant_local_name: str
    plant_english_name: str
    plant_botanical_name: str
    identification_confidence: float = Field(ge=0, le=100)

    health_status: Literal["healthy", "possibly_unhealthy", "uncertain"]
    detected_issue: str
    issue_type: Literal["none", "disease", "pest", "nutrient_like_symptom", "physical_damage", "uncertain"]
    severity: Literal["none", "low", "medium", "high", "uncertain"]
    symptoms: list[str]
    possible_causes: list[str]
    ai_solution: list[str]
    health_confidence: float = Field(ge=0, le=100)

    notes: list[str]


class FertilizerRecommendation(BaseModel):
    available: bool
    recommendation: str
    fertilizer_type: str
    application_guidance: str
    precautions: list[str]


class WateringRecommendation(BaseModel):
    available: bool
    requirement: str
    frequency: str
    guidance: list[str]


class PlantDoctorReport(BaseModel):
    vision: VisionAnalysis
    fertilizer: FertilizerRecommendation
    watering: WateringRecommendation
    database_match: bool
