"""SQLite database layer.

SRP: this module owns database connection, schema creation, seed data,
and read operations. It does not know anything about Streamlit or Groq.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SEED_PLANTS = [
    {
        "local_name": "Gulab / گلاب",
        "english_name": "Rose",
        "botanical_name": "Rosa",
        "fertilizer_type": "Balanced flowering-plant fertilizer; a rose fertilizer can also be used.",
        "fertilizer_guidance": "Follow the fertilizer product label. Avoid applying fertilizer to very dry or severely stressed plants.",
        "fertilizer_precautions": "Do not over-fertilize. Keep fertilizer away from direct contact with stems.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water when the upper soil layer begins to dry; frequency varies with season and growing conditions.",
        "watering_guidance": "Water the soil deeply enough to reach the root zone and avoid keeping the soil continuously waterlogged.",
        "disease_notes": "Common visible problems include black spot, powdery mildew, rust, aphids, and spider mites.",
    },
    {
        "local_name": "Tamatar / ٹماٹر",
        "english_name": "Tomato",
        "botanical_name": "Solanum lycopersicum",
        "fertilizer_type": "Tomato/vegetable fertilizer with balanced nutrients; flowering/fruiting formulations may be appropriate.",
        "fertilizer_guidance": "Follow the product label and avoid excessive nitrogen during fruiting.",
        "fertilizer_precautions": "Do not exceed label rates. Fertilizer choice should be adjusted after a soil test when possible.",
        "water_requirement": "Moderate to high",
        "watering_frequency": "Keep root-zone moisture reasonably consistent; check soil before watering.",
        "watering_guidance": "Water the soil rather than repeatedly wetting leaves. Avoid long periods of waterlogging.",
        "disease_notes": "Common visible problems include early blight, late blight, leaf spot, powdery mildew, and pest damage.",
    },
    {
        "local_name": "Mirch / مرچ",
        "english_name": "Chili pepper",
        "botanical_name": "Capsicum annuum",
        "fertilizer_type": "Balanced vegetable fertilizer; a fruiting formulation may be used according to the label.",
        "fertilizer_guidance": "Use label directions and avoid excessive nitrogen.",
        "fertilizer_precautions": "Do not over-fertilize. Adjust fertilizer based on soil testing when available.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water when the upper soil begins to dry; keep moisture reasonably consistent during flowering and fruiting.",
        "watering_guidance": "Avoid both severe drying and prolonged waterlogging.",
        "disease_notes": "Common problems include leaf spot, mosaic-like symptoms, aphids, thrips, and mites.",
    },
    {
        "local_name": "Aam / آم",
        "english_name": "Mango",
        "botanical_name": "Mangifera indica",
        "fertilizer_type": "Fruit-tree fertilizer appropriate for mangoes and the tree's growth stage.",
        "fertilizer_guidance": "Follow a product label designed for fruit trees; mature trees require different amounts than young trees.",
        "fertilizer_precautions": "Avoid applying excessive fertilizer. Soil testing is preferred for precise nutrient management.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water according to soil dryness and tree age; young trees generally need more regular watering than established trees.",
        "watering_guidance": "Water deeply around the root zone and avoid persistent waterlogging.",
        "disease_notes": "Common problems include powdery mildew, anthracnose, hoppers, scale insects, and leaf spots.",
    },
    {
        "local_name": "Amrood / امرود",
        "english_name": "Guava",
        "botanical_name": "Psidium guajava",
        "fertilizer_type": "Fruit-tree fertilizer appropriate for guava and its growth stage.",
        "fertilizer_guidance": "Follow the fertilizer label and adjust the program using soil-test information when possible.",
        "fertilizer_precautions": "Avoid excessive fertilizer and direct contact with the trunk.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water when the root-zone soil begins to dry; young trees usually need more frequent watering.",
        "watering_guidance": "Maintain reasonable moisture during active growth and fruit development without waterlogging.",
        "disease_notes": "Common problems include anthracnose, wilt, fruit flies, scale insects, and leaf spots.",
    },
    {
        "local_name": "Nimbu / لیموں",
        "english_name": "Lemon",
        "botanical_name": "Citrus limon",
        "fertilizer_type": "Citrus fertilizer or fruit-tree fertilizer suitable for lemon trees.",
        "fertilizer_guidance": "Follow the product label and consider soil testing for long-term nutrient management.",
        "fertilizer_precautions": "Avoid over-fertilization and direct fertilizer contact with the trunk.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water when the upper soil starts to dry; newly planted trees need more regular monitoring.",
        "watering_guidance": "Water deeply but allow excess water to drain away.",
        "disease_notes": "Common problems include leaf miner, aphids, scale insects, citrus canker-like symptoms, and fungal leaf problems.",
    },
    {
        "local_name": "Aloo / آلو",
        "english_name": "Potato",
        "botanical_name": "Solanum tuberosum",
        "fertilizer_type": "Potato/vegetable fertilizer selected according to soil test and crop stage.",
        "fertilizer_guidance": "Follow the product label. Avoid excessive nitrogen because it can favor foliage over tuber production.",
        "fertilizer_precautions": "Use soil testing when possible and never exceed label rates.",
        "water_requirement": "Moderate",
        "watering_frequency": "Keep soil moisture reasonably even during tuber formation; avoid prolonged waterlogging.",
        "watering_guidance": "Water the root zone and maintain good drainage.",
        "disease_notes": "Common problems include early blight, late blight, aphids, and other pest damage.",
    },
    {
        "local_name": "Gandum / گندم",
        "english_name": "Wheat",
        "botanical_name": "Triticum aestivum",
        "fertilizer_type": "Wheat/cereal fertilizer program based on soil testing and crop stage.",
        "fertilizer_guidance": "Use locally appropriate fertilizer recommendations and product labels.",
        "fertilizer_precautions": "Avoid blanket fertilizer rates when soil-test information is available.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water according to crop stage and local agronomic recommendations; do not rely on leaf appearance alone.",
        "watering_guidance": "Maintain adequate root-zone moisture while avoiding waterlogging.",
        "disease_notes": "Common problems include rusts, powdery mildew, aphids, and other cereal diseases/pests.",
    },
    {
        "local_name": "Kapas / کپاس",
        "english_name": "Cotton",
        "botanical_name": "Gossypium hirsutum",
        "fertilizer_type": "Cotton fertilizer program based on soil testing and crop stage.",
        "fertilizer_guidance": "Follow local agronomic recommendations and product labels.",
        "fertilizer_precautions": "Avoid excessive nitrogen and use soil testing when possible.",
        "water_requirement": "Moderate",
        "watering_frequency": "Water according to crop stage, soil moisture, and local agronomic guidance.",
        "watering_guidance": "Avoid prolonged waterlogging and severe moisture stress.",
        "disease_notes": "Common problems include bacterial blight, wilt, whitefly, aphids, thrips, and mites.",
    },
]


def _connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str) -> None:
    """Create tables and seed initial plant data if missing."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                local_name TEXT NOT NULL,
                english_name TEXT NOT NULL,
                botanical_name TEXT NOT NULL UNIQUE,
                fertilizer_type TEXT NOT NULL,
                fertilizer_guidance TEXT NOT NULL,
                fertilizer_precautions TEXT NOT NULL,
                water_requirement TEXT NOT NULL,
                watering_frequency TEXT NOT NULL,
                watering_guidance TEXT NOT NULL,
                disease_notes TEXT NOT NULL
            )
            """
        )

        for plant in SEED_PLANTS:
            conn.execute(
                """
                INSERT OR IGNORE INTO plants (
                    local_name, english_name, botanical_name,
                    fertilizer_type, fertilizer_guidance,
                    fertilizer_precautions, water_requirement,
                    watering_frequency, watering_guidance, disease_notes
                )
                VALUES (
                    :local_name, :english_name, :botanical_name,
                    :fertilizer_type, :fertilizer_guidance,
                    :fertilizer_precautions, :water_requirement,
                    :watering_frequency, :watering_guidance, :disease_notes
                )
                """,
                plant,
            )


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def get_plant_by_botanical_name(db_path: str, botanical_name: str) -> dict[str, Any] | None:
    """Exact-ish botanical-name lookup with a safe LIKE fallback."""
    query = botanical_name.strip()
    if not query:
        return None

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM plants WHERE lower(botanical_name) = lower(?)",
            (query,),
        ).fetchone()

        if row:
            return _row_to_dict(row)

        row = conn.execute(
            """
            SELECT * FROM plants
            WHERE lower(?) LIKE '%' || lower(botanical_name) || '%'
               OR lower(botanical_name) LIKE '%' || lower(?) || '%'
            ORDER BY length(botanical_name) ASC
            LIMIT 1
            """,
            (query, query),
        ).fetchone()

        return _row_to_dict(row)


def get_plant_by_english_name(db_path: str, english_name: str) -> dict[str, Any] | None:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM plants WHERE lower(english_name) = lower(?)",
            (english_name.strip(),),
        ).fetchone()
        return _row_to_dict(row)
