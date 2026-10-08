from __future__ import annotations

import json
import re
from pathlib import Path


SOURCE = Path(
    r"FoodInsightAI_FoodInsightLM_V0_2"
    r"\research\dataset\foodinsight_lm\v0_3"
    r"\foodinsight_usda_v0_3.jsonl"
)

OUTPUT = Path(r"backend\data\usda\usda_evidence_v03.jsonl")


NUTRIENT_NAMES = (
    "Protein",
    "Total lipid",
    "Carbohydrate",
    "Water",
    "Fiber",
    "Calcium",
    "Iron",
    "Magnesium",
    "Phosphorus",
    "Potassium",
    "Sodium",
    "Zinc",
    "Vitamin C",
)


def parse_context(context: str) -> tuple[str, str, str, dict, dict]:
    lines = [line.strip() for line in context.splitlines() if line.strip()]

    food_name = ""
    food_id = ""
    category = ""
    nutrients: dict[str, dict[str, object]] = {}
    portions: dict[str, float] = {}

    for line in lines:
        if line.startswith("Food: "):
            food_name = line[len("Food: "):]

        elif line.startswith("Food ID: "):
            food_id = line[len("Food ID: "):]

        elif line.startswith("Category: "):
            category = line[len("Category: "):]

        elif line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)

            if key.startswith(NUTRIENT_NAMES):
                parts = value.split()

                if len(parts) >= 2:
                    try:
                        nutrients[key] = {
                            "value_per_100g": float(parts[0]),
                            "unit": parts[1],
                        }
                    except ValueError:
                        pass

            elif re.fullmatch(r"\d+", key):
                parts = value.split()

                if parts:
                    try:
                        portions[key] = float(parts[0])
                    except ValueError:
                        pass

    return food_name, food_id, category, nutrients, portions


OUTPUT.parent.mkdir(parents=True, exist_ok=True)

seen: set[tuple[str, str]] = set()
written = 0

with SOURCE.open("r", encoding="utf-8") as src, OUTPUT.open(
    "w", encoding="utf-8"
) as dst:
    for line in src:
        row = json.loads(line)

        food_ids = row.get("food_ids") or []
        context = row.get("context", "")

        if not food_ids or not context:
            continue

        food_id = str(food_ids[0])
        key = (food_id, context)

        if key in seen:
            continue

        seen.add(key)

        food_name, parsed_food_id, category, nutrients, portions = parse_context(
            context
        )

        if not parsed_food_id:
            parsed_food_id = food_id

        record = {
            "evidence_id": f"usda_{parsed_food_id}_primary",
            "food_id": parsed_food_id,
            "food_name": food_name,
            "category": category,
            "source": row.get("source", "USDA FoodData Central FNDDS"),
            "nutrients": nutrients,
            "portions": portions,
            "context": context,
        }

        dst.write(json.dumps(record, ensure_ascii=False) + "\n")
        written += 1

print(f"records_written: {written}")
print(f"output: {OUTPUT}")
