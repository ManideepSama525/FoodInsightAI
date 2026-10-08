from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_PATH = (
    ROOT
    / "research"
    / "datasets"
    / "usda"
    / "foundation_2026_04"
    / "FoodData_Central_foundation_food_json_2026-04-30.json"
)

FNDDS_PATH = (
    ROOT
    / "research"
    / "datasets"
    / "usda"
    / "fndds_2021_2023"
    / "surveyDownload.json"
)

NORMALIZED_DIR = (
    ROOT / "research" / "datasets" / "foodinsight_normalized"
)

OUTPUT_DIR = (
    ROOT / "research" / "dataset" / "foodinsight_lm" / "v0_2"
)

SEED = 20261001

TARGET_NUTRIENTS = [
    "Protein",
    "Water",
    "Total lipid (fat)",
    "Carbohydrate, by difference",
    "Fiber, total dietary",
    "Calcium, Ca",
    "Iron, Fe",
    "Magnesium, Mg",
    "Phosphorus, P",
    "Potassium, K",
    "Sodium, Na",
    "Zinc, Zn",
    "Vitamin C, total ascorbic acid",
]

NUTRIENT_ALIASES = {
    "protein": "Protein",
    "water": "Water",
    "total lipid (fat)": "Total lipid (fat)",
    "carbohydrate, by difference": "Carbohydrate, by difference",
    "fiber, total dietary": "Fiber, total dietary",
    "calcium, ca": "Calcium, Ca",
    "iron, fe": "Iron, Fe",
    "magnesium, mg": "Magnesium, Mg",
    "phosphorus, p": "Phosphorus, P",
    "potassium, k": "Potassium, K",
    "sodium, na": "Sodium, Na",
    "zinc, zn": "Zinc, Zn",
    "vitamin c, total ascorbic acid": "Vitamin C, total ascorbic acid",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def clean_text(value) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def safe_number(value):
    if value is None:
        return None

    try:
        number = float(value)

        if number != number:
            return None

        return number

    except (TypeError, ValueError):
        return None


def normalize_nutrient_name(name: str) -> str | None:
    key = clean_text(name).lower()
    return NUTRIENT_ALIASES.get(key)


def normalize_foundation_food(food: dict) -> dict | None:
    if not isinstance(food, dict):
        return None

    fdc_id = food.get("fdcId")

    if fdc_id is None:
        return None

    description = clean_text(food.get("description"))

    if not description:
        return None

    nutrients = []

    for item in food.get("foodNutrients") or []:
        if not isinstance(item, dict):
            continue

        nutrient = item.get("nutrient") or {}

        if not isinstance(nutrient, dict):
            continue

        name = clean_text(nutrient.get("name"))
        normalized_name = normalize_nutrient_name(name)

        if normalized_name is None:
            continue

        amount = safe_number(item.get("amount"))

        if amount is None:
            continue

        nutrients.append(
            {
                "nutrient_id": nutrient.get("id"),
                "nutrient_number": nutrient.get("number"),
                "name": normalized_name,
                "unit": clean_text(nutrient.get("unitName")),
                "amount": amount,
                "median": safe_number(item.get("median")),
                "data_points": item.get("dataPoints"),
                "derivation": item.get(
                    "foodNutrientDerivation"
                ) or {},
            }
        )

    portions = []

    for portion in food.get("foodPortions") or []:
        if not isinstance(portion, dict):
            continue

        gram_weight = safe_number(
            portion.get("gramWeight")
        )

        portions.append(
            {
                "portion_id": portion.get("id"),
                "description": clean_text(
                    portion.get("portionDescription")
                ),
                "gram_weight": gram_weight,
                "amount": safe_number(
                    portion.get("amount")
                ),
                "unit": clean_text(
                    (
                        portion.get("measureUnit")
                        or {}
                    ).get("name")
                ),
                "modifier": clean_text(
                    portion.get("modifier")
                ),
            }
        )

    category = food.get("foodCategory") or {}

    if isinstance(category, dict):
        category_name = clean_text(
            category.get("description")
        )
    else:
        category_name = clean_text(category)

    return {
        "food_id": f"foundation:{fdc_id}",
        "source_dataset": "USDA Foundation Foods",
        "source_release": "2026-04",
        "source_id": fdc_id,
        "description": description,
        "category": category_name,
        "data_type": clean_text(
            food.get("dataType")
        ),
        "publication_date": clean_text(
            food.get("publicationDate")
        ),
        "historical_reference": bool(
            food.get(
                "isHistoricalReference",
                False,
            )
        ),
        "nutrients": nutrients,
        "portions": portions,
        "input_foods": (
            food.get("inputFoods")
            if isinstance(
                food.get("inputFoods"),
                list,
            )
            else []
        ),
        "food_attributes": (
            food.get("foodAttributes")
            if isinstance(
                food.get("foodAttributes"),
                list,
            )
            else []
        ),
        "provenance": {
            "publisher": (
                "USDA Agricultural Research Service"
            ),
            "dataset": (
                "FoodData Central Foundation Foods"
            ),
            "release": "2026-04",
            "source_record_id": fdc_id,
        },
    }


def normalize_fndds_food(food: dict) -> dict | None:
    if not isinstance(food, dict):
        return None

    fdc_id = food.get("fdcId")

    if fdc_id is None:
        return None

    description = clean_text(food.get("description"))

    if not description:
        return None

    nutrients = []

    for item in food.get("foodNutrients") or []:
        if not isinstance(item, dict):
            continue

        nutrient = item.get("nutrient") or {}

        if not isinstance(nutrient, dict):
            continue

        name = clean_text(nutrient.get("name"))
        normalized_name = normalize_nutrient_name(name)

        if normalized_name is None:
            continue

        amount = safe_number(item.get("amount"))

        if amount is None:
            continue

        nutrients.append(
            {
                "nutrient_id": nutrient.get("id"),
                "nutrient_number": nutrient.get("number"),
                "name": normalized_name,
                "unit": clean_text(
                    nutrient.get("unitName")
                ),
                "amount": amount,
            }
        )

    portions = []

    for portion in food.get("foodPortions") or []:
        if not isinstance(portion, dict):
            continue

        portions.append(
            {
                "portion_id": portion.get("id"),
                "description": clean_text(
                    portion.get("portionDescription")
                ),
                "gram_weight": safe_number(
                    portion.get("gramWeight")
                ),
                "amount": safe_number(
                    portion.get("amount")
                ),
                "unit": clean_text(
                    (
                        portion.get("measureUnit")
                        or {}
                    ).get("name")
                ),
                "modifier": clean_text(
                    portion.get("modifier")
                ),
            }
        )

    category = food.get(
        "wweiaFoodCategory"
    ) or {}

    if isinstance(category, dict):
        category_name = clean_text(
            category.get(
                "wweiaFoodCategoryDescription"
            )
        )
        category_code = category.get(
            "wweiaFoodCategoryCode"
        )
    else:
        category_name = clean_text(category)
        category_code = None

    return {
        "food_id": f"fndds:{fdc_id}",
        "source_dataset": "USDA FNDDS",
        "source_release": "2021-2023",
        "source_id": fdc_id,
        "food_code": food.get("foodCode"),
        "description": description,
        "category": category_name,
        "category_code": category_code,
        "data_type": clean_text(
            food.get("dataType")
        ),
        "start_date": clean_text(
            food.get("startDate")
        ),
        "end_date": clean_text(
            food.get("endDate")
        ),
        "publication_date": clean_text(
            food.get("publicationDate")
        ),
        "footnote": clean_text(
            food.get("footnote")
        ),
        "nutrients": nutrients,
        "portions": portions,
        "input_foods": (
            food.get("inputFoods")
            if isinstance(
                food.get("inputFoods"),
                list,
            )
            else []
        ),
        "food_attributes": (
            food.get("foodAttributes")
            if isinstance(
                food.get("foodAttributes"),
                list,
            )
            else []
        ),
        "provenance": {
            "publisher": (
                "USDA Agricultural Research Service"
            ),
            "dataset": (
                "FoodData Central FNDDS"
            ),
            "release": "2021-2023",
            "source_record_id": fdc_id,
        },
    }


def nutrient_map(food: dict) -> dict:
    result = {}

    for nutrient in food.get("nutrients", []):
        name = nutrient.get("name")

        if (
            name
            and nutrient.get("amount") is not None
        ):
            result[name] = nutrient

    return result


def make_direct_task(
    food: dict,
    nutrient: dict,
    index: int,
) -> dict:
    amount = nutrient["amount"]
    unit = nutrient["unit"]
    name = nutrient["name"]

    answer = (
        f"{food['description']} provides "
        f"{amount:g} {unit} of {name} per 100 g."
    )

    context = (
        f"USDA {food['source_dataset']} record "
        f"{food['source_id']}: "
        f"{food['description']}. "
        f"{name} = {amount:g} {unit} per 100 g."
    )

    return {
        "id": (
            f"{food['food_id']}:"
            f"direct:{index}"
        ),
        "task_family": "direct_nutrient_qa",
        "source_dataset": food[
            "source_dataset"
        ],
        "food_ids": [
            food["food_id"]
        ],
        "question": (
            f"How much {name} does "
            f"{food['description']} contain "
            f"per 100 g?"
        ),
        "context": context,
        "answer": answer,
        "claims": [
            {
                "claim": answer,
                "evidence_ids": [
                    food["food_id"]
                ],
            }
        ],
        "evidence_ids": [
            food["food_id"]
        ],
        "provenance": food[
            "provenance"
        ],
    }


def make_portion_task(
    food: dict,
    portion: dict,
    index: int,
) -> dict | None:
    description = clean_text(
        portion.get("description")
    )
    gram_weight = portion.get(
        "gram_weight"
    )

    if not description:
        return None

    if gram_weight is None:
        return None

    if gram_weight <= 0:
        return None

    answer = (
        f"The USDA record gives "
        f"{gram_weight:g} g for "
        f"{description} of "
        f"{food['description']}."
    )

    return {
        "id": (
            f"{food['food_id']}:"
            f"portion:{index}"
        ),
        "task_family": "portion_reasoning",
        "source_dataset": food[
            "source_dataset"
        ],
        "food_ids": [
            food["food_id"]
        ],
        "question": (
            f"What is the gram weight of "
            f"{description} of "
            f"{food['description']}?"
        ),
        "context": (
            f"Food: {food['description']}; "
            f"portion: {description}; "
            f"gram weight: {gram_weight:g} g."
        ),
        "answer": answer,
        "claims": [
            {
                "claim": answer,
                "evidence_ids": [
                    food["food_id"]
                ],
            }
        ],
        "evidence_ids": [
            food["food_id"]
        ],
        "provenance": food[
            "provenance"
        ],
    }


def make_category_task(
    food: dict,
) -> dict | None:
    category = clean_text(
        food.get("category")
    )

    if not category:
        return None

    answer = (
        f"{food['description']} is "
        f"categorized as {category} "
        f"in the USDA source record."
    )

    return {
        "id": (
            f"{food['food_id']}:"
            "category:0"
        ),
        "task_family": "category_evidence",
        "source_dataset": food[
            "source_dataset"
        ],
        "food_ids": [
            food["food_id"]
        ],
        "question": (
            f"What USDA category is "
            f"associated with "
            f"{food['description']}?"
        ),
        "context": (
            f"Food: {food['description']}; "
            f"USDA category: {category}."
        ),
        "answer": answer,
        "claims": [
            {
                "claim": answer,
                "evidence_ids": [
                    food["food_id"]
                ],
            }
        ],
        "evidence_ids": [
            food["food_id"]
        ],
        "provenance": food[
            "provenance"
        ],
    }


def make_rejection_task(
    food: dict,
    absent_nutrient: str,
) -> dict:
    answer = (
        f"The supplied USDA evidence does "
        f"not establish a usable "
        f"{absent_nutrient} value for "
        f"{food['description']}."
    )

    return {
        "id": (
            f"{food['food_id']}:"
            f"rejection:{absent_nutrient}"
        ),
        "task_family": (
            "evidence_bounded_rejection"
        ),
        "source_dataset": food[
            "source_dataset"
        ],
        "food_ids": [
            food["food_id"]
        ],
        "question": (
            f"Does the supplied USDA evidence "
            f"establish the amount of "
            f"{absent_nutrient} in "
            f"{food['description']}?"
        ),
        "context": (
            f"Food: {food['description']}. "
            f"The normalized record does not "
            f"contain a usable value for "
            f"{absent_nutrient}."
        ),
        "answer": answer,
        "claims": [
            {
                "claim": answer,
                "evidence_ids": [
                    food["food_id"]
                ],
            }
        ],
        "evidence_ids": [
            food["food_id"]
        ],
        "provenance": food[
            "provenance"
        ],
    }


def unique_tasks(
    tasks: list[dict],
) -> list[dict]:
    seen = set()
    result = []

    for task in tasks:
        key = (
            task["task_family"],
            task["question"]
            .strip()
            .lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(task)

    return result


def split_foods(
    foods: list[dict],
):
    rng = random.Random(SEED)

    food_ids = sorted(
        {
            food["food_id"]
            for food in foods
            if food.get("food_id")
        }
    )

    rng.shuffle(food_ids)

    total = len(food_ids)

    train_end = int(
        total * 0.80
    )

    validation_end = int(
        total * 0.90
    )

    train_ids = set(
        food_ids[:train_end]
    )

    validation_ids = set(
        food_ids[
            train_end:validation_end
        ]
    )

    test_ids = set(
        food_ids[
            validation_end:
        ]
    )

    return (
        train_ids,
        validation_ids,
        test_ids,
    )


def write_jsonl(
    path: Path,
    records: list[dict],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for record in records:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def load_json(
    path: Path,
) -> dict:
    print(
        f"Loading: {path.name}"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def main():
    print("=" * 72)
    print(
        "FOODINSIGHT-LM V0.2 DATASET BUILDER"
    )
    print("=" * 72)

    if not FOUNDATION_PATH.exists():
        raise FileNotFoundError(
            f"Foundation dataset not found:\n"
            f"{FOUNDATION_PATH}"
        )

    if not FNDDS_PATH.exists():
        raise FileNotFoundError(
            f"FNDDS dataset not found:\n"
            f"{FNDDS_PATH}"
        )

    foundation_json = load_json(
        FOUNDATION_PATH
    )

    fndds_json = load_json(
        FNDDS_PATH
    )

    foundation_records = (
        foundation_json.get(
            "FoundationFoods",
            [],
        )
    )

    fndds_records = (
        fndds_json.get(
            "SurveyFoods",
            [],
        )
    )

    print(
        f"Foundation raw records: "
        f"{len(foundation_records)}"
    )

    print(
        f"FNDDS raw records: "
        f"{len(fndds_records)}"
    )

    normalized = []

    invalid_foundation = 0
    invalid_fndds = 0

    foundation_null_records = 0
    fndds_null_records = 0

    for food in foundation_records:
        if not isinstance(food, dict):
            foundation_null_records += 1
            invalid_foundation += 1
            continue

        normalized_food = (
            normalize_foundation_food(
                food
            )
        )

        if normalized_food is None:
            invalid_foundation += 1
            continue

        normalized.append(
            normalized_food
        )

    for food in fndds_records:
        if not isinstance(food, dict):
            fndds_null_records += 1
            invalid_fndds += 1
            continue

        normalized_food = (
            normalize_fndds_food(
                food
            )
        )

        if normalized_food is None:
            invalid_fndds += 1
            continue

        normalized.append(
            normalized_food
        )

    print(
        f"Normalized Foundation foods: "
        f"{len(foundation_records) - invalid_foundation}"
    )

    print(
        f"Normalized FNDDS foods: "
        f"{len(fndds_records) - invalid_fndds}"
    )

    print(
        f"Skipped Foundation records: "
        f"{invalid_foundation}"
    )

    print(
        f"Skipped FNDDS records: "
        f"{invalid_fndds}"
    )

    NORMALIZED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    normalized_path = (
        NORMALIZED_DIR
        / "foodinsight_usda_normalized_v0_2.jsonl"
    )

    write_jsonl(
        normalized_path,
        normalized,
    )

    print(
        f"Normalized records written: "
        f"{len(normalized)}"
    )

    train_ids, validation_ids, test_ids = (
        split_foods(normalized)
    )

    tasks = []

    for food in normalized:
        nutrients = nutrient_map(
            food
        )

        available_targets = [
            nutrient
            for nutrient in TARGET_NUTRIENTS
            if nutrient in nutrients
        ]

        # -------------------------------------------------
        # 1. Direct nutrient QA
        # -------------------------------------------------

        for index, nutrient_name in enumerate(
            available_targets
        ):
            tasks.append(
                make_direct_task(
                    food,
                    nutrients[
                        nutrient_name
                    ],
                    index,
                )
            )

        # -------------------------------------------------
        # 2. Portion reasoning
        # -------------------------------------------------

        for index, portion in enumerate(
            food.get("portions", [])
        ):
            task = make_portion_task(
                food,
                portion,
                index,
            )

            if task:
                tasks.append(task)

        # -------------------------------------------------
        # 3. Category evidence
        # -------------------------------------------------

        category_task = (
            make_category_task(food)
        )

        if category_task:
            tasks.append(
                category_task
            )

        # -------------------------------------------------
        # 4. Evidence-bounded rejection
        # -------------------------------------------------

        absent_targets = [
            nutrient
            for nutrient in TARGET_NUTRIENTS
            if nutrient not in nutrients
        ]

        if (
            available_targets
            and absent_targets
        ):
            # Keep this bounded: one deterministic
            # rejection task per food.
            tasks.append(
                make_rejection_task(
                    food,
                    absent_targets[0],
                )
            )

    tasks = unique_tasks(
        tasks
    )

    print()
    print(
        f"Unique tasks: {len(tasks)}"
    )

    task_counts = Counter(
        task["task_family"]
        for task in tasks
    )

    print(
        "Task distribution:"
    )

    for family, count in sorted(
        task_counts.items()
    ):
        print(
            f"  {family}: {count}"
        )

    train_tasks = []
    validation_tasks = []
    test_tasks = []

    for task in tasks:
        food_ids = task.get(
            "food_ids",
            [],
        )

        if not food_ids:
            continue

        food_id = food_ids[0]

        if food_id in train_ids:
            train_tasks.append(task)

        elif food_id in validation_ids:
            validation_tasks.append(task)

        elif food_id in test_ids:
            test_tasks.append(task)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    train_path = (
        OUTPUT_DIR
        / "foodinsight_usda_v0_2_train.jsonl"
    )

    validation_path = (
        OUTPUT_DIR
        / "foodinsight_usda_v0_2_validation.jsonl"
    )

    test_path = (
        OUTPUT_DIR
        / "foodinsight_usda_v0_2_test.jsonl"
    )

    all_path = (
        OUTPUT_DIR
        / "foodinsight_usda_v0_2.jsonl"
    )

    write_jsonl(
        train_path,
        train_tasks,
    )

    write_jsonl(
        validation_path,
        validation_tasks,
    )

    write_jsonl(
        test_path,
        test_tasks,
    )

    write_jsonl(
        all_path,
        tasks,
    )

    source_counts = Counter(
        food["source_dataset"]
        for food in normalized
    )

    nutrient_record_count = sum(
        bool(
            food.get("nutrients")
        )
        for food in normalized
    )

    portion_record_count = sum(
        bool(
            food.get("portions")
        )
        for food in normalized
    )

    metadata = {
        "dataset_name": (
            "FoodInsight-LM V0.2"
        ),
        "created_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "seed": SEED,
        "status": (
            "experiment_corpus"
        ),
        "source_datasets": {
            "foundation": {
                "publisher": (
                    "USDA Agricultural "
                    "Research Service"
                ),
                "dataset": (
                    "FoodData Central "
                    "Foundation Foods"
                ),
                "release": "2026-04",
                "records": len(
                    foundation_records
                ),
                "sha256": sha256(
                    FOUNDATION_PATH
                ),
            },
            "fndds": {
                "publisher": (
                    "USDA Agricultural "
                    "Research Service"
                ),
                "dataset": (
                    "FoodData Central FNDDS"
                ),
                "release": "2021-2023",
                "records": len(
                    fndds_records
                ),
                "sha256": sha256(
                    FNDDS_PATH
                ),
            },
        },
        "normalized_records": len(
            normalized
        ),
        "normalized_records_with_nutrients": (
            nutrient_record_count
        ),
        "normalized_records_with_portions": (
            portion_record_count
        ),
        "invalid_records": {
            "foundation": invalid_foundation,
            "fndds": invalid_fndds,
        },
        "null_records": {
            "foundation": foundation_null_records,
            "fndds": fndds_null_records,
        },
        "target_nutrients": (
            TARGET_NUTRIENTS
        ),
        "task_counts": dict(
            task_counts
        ),
        "source_record_counts": dict(
            source_counts
        ),
        "split": {
            "strategy": (
                "food/entity-level isolation"
            ),
            "train_foods": len(
                train_ids
            ),
            "validation_foods": len(
                validation_ids
            ),
            "test_foods": len(
                test_ids
            ),
            "train_tasks": len(
                train_tasks
            ),
            "validation_tasks": len(
                validation_tasks
            ),
            "test_tasks": len(
                test_tasks
            ),
        },
        "files": {
            "normalized": str(
                normalized_path.relative_to(
                    ROOT
                )
            ),
            "all_tasks": str(
                all_path.relative_to(
                    ROOT
                )
            ),
            "train": str(
                train_path.relative_to(
                    ROOT
                )
            ),
            "validation": str(
                validation_path.relative_to(
                    ROOT
                )
            ),
            "test": str(
                test_path.relative_to(
                    ROOT
                )
            ),
        },
        "provenance": {
            "publisher": (
                "USDA Agricultural "
                "Research Service"
            ),
            "source": (
                "USDA FoodData Central"
            ),
            "derived_by": (
                "FoodInsightAI V0.2 "
                "dataset builder"
            ),
            "license_note": (
                "Retain USDA provenance "
                "and source release metadata "
                "in derived artifacts."
            ),
        },
        "quality_notes": [
            (
                "Raw USDA JSON files are "
                "never modified."
            ),
            (
                "Malformed/null source records "
                "are skipped and counted."
            ),
            (
                "Food/entity-level split prevents "
                "the same normalized food_id from "
                "appearing across train, validation, "
                "and test."
            ),
            (
                "V0.2 is an experiment corpus and "
                "must pass independent validation "
                "before model training."
            ),
        ],
    }

    metadata_path = (
        OUTPUT_DIR
        / "foodinsight_usda_v0_2_metadata.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print(
        "FOODINSIGHT DATASET V0.2: OK"
    )
    print("=" * 72)

    print(
        f"Normalized records: "
        f"{len(normalized)}"
    )

    print(
        f"Total tasks: "
        f"{len(tasks)}"
    )

    print(
        f"Train tasks: "
        f"{len(train_tasks)}"
    )

    print(
        f"Validation tasks: "
        f"{len(validation_tasks)}"
    )

    print(
        f"Test tasks: "
        f"{len(test_tasks)}"
    )

    print(
        f"Metadata: "
        f"{metadata_path}"
    )


if __name__ == "__main__":
    main()