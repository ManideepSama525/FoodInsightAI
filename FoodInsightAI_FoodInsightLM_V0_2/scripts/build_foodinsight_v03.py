from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

NORMALIZED_PATH = (
    ROOT
    / "research"
    / "datasets"
    / "foodinsight_normalized"
    / "foodinsight_usda_normalized_v0_2.jsonl"
)

V02_DIR = (
    ROOT
    / "research"
    / "dataset"
    / "foodinsight_lm"
    / "v0_2"
)

OUT_DIR = (
    ROOT
    / "research"
    / "dataset"
    / "foodinsight_lm"
    / "v0_3"
)

SEED = 20261002

TARGETS = {
    "direct_nutrient_qa": 12000,
    "numerical_reasoning": 10000,
    "portion_reasoning": 10000,
    "multi_food_comparison": 8000,
    "evidence_selection": 7000,
    "evidence_sufficiency": 7000,
    "evidence_bounded_rejection": 7000,
    "missing_value_uncertainty": 5000,
    "provenance_reasoning": 5000,
    "source_aware_comparison": 4000,
}


def stable_id(*parts: Any) -> str:
    payload = "||".join(str(x) for x in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return " ".join(value.split()).strip()

    return str(value).strip()


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def first_value(record: dict, *keys: str) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def food_id(record: dict) -> str:
    value = first_value(
        record,
        "fdc_id",
        "fdcId",
        "food_id",
        "foodId",
    )

    if value is None:
        value = stable_id(
            first_value(record, "description", "food"),
            first_value(record, "data_type", "dataType"),
        )

    return str(value)


def food_name(record: dict) -> str:
    return clean_text(
        first_value(
            record,
            "description",
            "food",
            "food_name",
            "foodName",
        )
        or "Unknown food"
    )


def source_name(record: dict) -> str:
    value = first_value(
        record,
        "source",
        "source_name",
        "data_source",
    )

    if value:
        return clean_text(value)

    data_type = clean_text(
        first_value(record, "data_type", "dataType")
    )

    if "foundation" in data_type.lower():
        return "USDA FoodData Central Foundation Foods"

    if "survey" in data_type.lower():
        return "USDA FoodData Central FNDDS"

    return "USDA FoodData Central"


def get_category(record: dict) -> str:
    value = first_value(
        record,
        "food_category",
        "foodCategory",
        "category",
        "wweia_food_category",
        "wweiaFoodCategory",
    )

    if isinstance(value, dict):
        value = (
            value.get("description")
            or value.get("name")
            or value.get("code")
        )

    return clean_text(value)


def get_portions(record: dict) -> list[dict]:
    value = first_value(
        record,
        "food_portions",
        "foodPortions",
        "portions",
    )

    if not isinstance(value, list):
        return []

    return [x for x in value if isinstance(x, dict)]


def portion_grams(portion: dict) -> float | None:
    value = first_value(
        portion,
        "gram_weight",
        "gramWeight",
        "weight",
        "grams",
    )

    if finite_number(value) and float(value) > 0:
        return float(value)

    return None


def portion_description(portion: dict) -> str:
    return clean_text(
        first_value(
            portion,
            "portion_description",
            "portionDescription",
            "modifier",
            "measure_unit",
            "measureUnit",
            "amount",
        )
        or "serving"
    )


def get_nutrients(record: dict) -> list[dict]:
    value = first_value(
        record,
        "food_nutrients",
        "foodNutrients",
        "nutrients",
    )

    if not isinstance(value, list):
        return []

    return [x for x in value if isinstance(x, dict)]


def nutrient_name(nutrient: dict) -> str:
    nested = nutrient.get("nutrient")

    if isinstance(nested, dict):
        value = (
            nested.get("name")
            or nested.get("nutrientName")
        )

        if value:
            return clean_text(value)

    return clean_text(
        first_value(
            nutrient,
            "nutrient_name",
            "nutrientName",
            "name",
        )
    )


def nutrient_unit(nutrient: dict) -> str:
    nested = nutrient.get("nutrient")

    if isinstance(nested, dict):
        value = (
            nested.get("unit_name")
            or nested.get("unitName")
            or nested.get("unit")
        )

        if value:
            return clean_text(value)

    return clean_text(
        first_value(
            nutrient,
            "unit_name",
            "unitName",
            "unit",
        )
    )


def nutrient_amount(nutrient: dict) -> float | None:
    for key in ("amount", "median", "value"):
        value = nutrient.get(key)

        if finite_number(value):
            return float(value)

    nested = nutrient.get("nutrient")

    if isinstance(nested, dict):
        value = nested.get("amount")

        if finite_number(value):
            return float(value)

    return None


def normalize_record(record: dict) -> dict:
    nutrients = []

    for nutrient in get_nutrients(record):
        name = nutrient_name(nutrient)
        amount = nutrient_amount(nutrient)
        unit = nutrient_unit(nutrient)

        if not name:
            continue

        nutrients.append(
            {
                "name": name,
                "amount": amount,
                "unit": unit,
            }
        )

    portions = []

    for portion in get_portions(record):
        portions.append(
            {
                "description": portion_description(portion),
                "grams": portion_grams(portion),
            }
        )

    return {
        "food_id": food_id(record),
        "food_name": food_name(record),
        "category": get_category(record),
        "source": source_name(record),
        "data_type": clean_text(
            first_value(
                record,
                "data_type",
                "dataType",
            )
        ),
        "nutrients": nutrients,
        "portions": portions,
        "raw": record,
    }


def make_task(
    task_family: str,
    question: str,
    context: str,
    answer: str,
    evidence_ids: list[str],
    food_ids: list[str],
    source: str,
    metadata: dict | None = None,
) -> dict:

    ids = list(
        dict.fromkeys(
            str(x) for x in food_ids
        )
    )

    task_id = stable_id(
        task_family,
        question,
        context,
        answer,
        *ids,
    )

    row = {
        "task_id": f"v03_{task_id}",
        "task_family": task_family,
        "question": question,
        "context": context,
        "answer": answer,
        "evidence_ids": list(
            dict.fromkeys(evidence_ids)
        ),
        "food_ids": ids,
        "source": source,
        "claims": [
            {
                "claim": answer,
                "evidence_ids": list(
                    dict.fromkeys(evidence_ids)
                ),
            }
        ],
        "dataset_version": "v0.3",
    }

    if metadata:
        row["metadata"] = metadata

    return row


def evidence_id(
    food: dict,
    suffix: str = "primary",
) -> str:
    return f"usda_{food['food_id']}_{suffix}"


def food_context(food: dict) -> str:
    nutrient_lines = []

    for n in food["nutrients"][:80]:
        amount = n["amount"]
        unit = n["unit"]

        if amount is None:
            value = "not reported"
        else:
            value = f"{amount:g} {unit}".strip()

        nutrient_lines.append(
            f"- {n['name']}: {value}"
        )

    portion_lines = []

    for p in food["portions"][:12]:
        grams = p["grams"]

        if grams is None:
            portion_lines.append(
                f"- {p['description']}: "
                "gram weight not reported"
            )
        else:
            portion_lines.append(
                f"- {p['description']}: "
                f"{grams:g} g"
            )

    return (
        f"Food: {food['food_name']}\n"
        f"Food ID: {food['food_id']}\n"
        f"Category: "
        f"{food['category'] or 'not reported'}\n"
        f"Source: {food['source']}\n"
        f"Nutrients:\n"
        f"{chr(10).join(nutrient_lines) or '- none reported'}\n"
        f"Portions:\n"
        f"{chr(10).join(portion_lines) or '- none reported'}"
    )


def nutrient_candidates(food: dict) -> list[dict]:
    return [
        n
        for n in food["nutrients"]
        if (
            n["amount"] is not None
            and n["name"]
            and n["unit"]
        )
    ]


def nutrient_map(food: dict) -> dict[str, dict]:
    result = {}

    for n in nutrient_candidates(food):
        key = n["name"].lower()

        if key not in result:
            result[key] = n

    return result


def build_direct_nutrient_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    candidates = []

    for food in foods:
        for nutrient in nutrient_candidates(food):
            candidates.append(
                (food, nutrient)
            )

    rng.shuffle(candidates)

    tasks = []

    for food, nutrient in candidates[:target]:
        name = nutrient["name"]
        amount = nutrient["amount"]
        unit = nutrient["unit"]

        question = (
            f"How much {name} does "
            f"{food['food_name']} contain?"
        )

        answer = (
            f"{food['food_name']} contains "
            f"{amount:g} {unit} of {name} "
            "according to the USDA evidence provided."
        )

        tasks.append(
            make_task(
                "direct_nutrient_qa",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
                {
                    "nutrient": name,
                    "unit": unit,
                },
            )
        )

    return tasks


def build_numerical_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    candidates = []

    for food in foods:
        for nutrient in nutrient_candidates(food):
            for portion in food["portions"]:
                if portion["grams"] is not None:
                    candidates.append(
                        (
                            food,
                            nutrient,
                            portion,
                        )
                    )

    rng.shuffle(candidates)

    tasks = []

    for food, nutrient, portion in candidates[:target]:
        grams = portion["grams"]
        amount = nutrient["amount"]

        scaled = amount * grams / 100.0

        question = (
            "Using the USDA value per 100 g, "
            f"approximately how much "
            f"{nutrient['name']} is in {grams:g} g "
            f"of {food['food_name']}?"
        )

        answer = (
            f"Approximately {scaled:.3f} "
            f"{nutrient['unit']} of "
            f"{nutrient['name']}, calculated from "
            f"{amount:g} {nutrient['unit']} per 100 g "
            f"and a {grams:g} g portion."
        )

        tasks.append(
            make_task(
                "numerical_reasoning",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
                {
                    "nutrient": nutrient["name"],
                    "portion_grams": grams,
                    "calculation": (
                        f"{amount} * {grams} / 100"
                    ),
                },
            )
        )

    return tasks


def build_portion_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    candidates = []

    for food in foods:
        portions = [
            p
            for p in food["portions"]
            if p["grams"] is not None
        ]

        if portions:
            candidates.append(
                (food, portions)
            )

    rng.shuffle(candidates)

    tasks = []

    for food, portions in candidates:
        if len(tasks) >= target:
            break

        for portion in portions:
            if len(tasks) >= target:
                break

            question = (
                "What gram weight does the USDA record "
                "associate with the portion "
                f"'{portion['description']}' for "
                f"{food['food_name']}?"
            )

            answer = (
                "The recorded gram weight is "
                f"{portion['grams']:g} g."
            )

            tasks.append(
                make_task(
                    "portion_reasoning",
                    question,
                    food_context(food),
                    answer,
                    [evidence_id(food)],
                    [food["food_id"]],
                    food["source"],
                    {
                        "portion": (
                            portion["description"]
                        ),
                        "grams": portion["grams"],
                    },
                )
            )

    return tasks


def build_multi_food_comparison_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    usable = []

    for food in foods:
        mapping = nutrient_map(food)

        if mapping:
            usable.append(
                (food, mapping)
            )

    by_category = defaultdict(list)

    for item in usable:
        category = (
            item[0]["category"]
            or "uncategorized"
        )
        by_category[category].append(item)

    pairs = []

    for category_items in by_category.values():
        if len(category_items) < 2:
            continue

        shuffled = category_items[:]
        rng.shuffle(shuffled)

        for i in range(
            0,
            len(shuffled) - 1,
            2,
        ):
            pairs.append(
                (
                    shuffled[i],
                    shuffled[i + 1],
                )
            )

    rng.shuffle(pairs)

    tasks = []

    for (food_a, map_a), (
        food_b,
        map_b,
    ) in pairs:

        if len(tasks) >= target:
            break

        common = sorted(
            set(map_a) & set(map_b)
        )

        if not common:
            continue

        nutrient_key = rng.choice(common)

        a = map_a[nutrient_key]
        b = map_b[nutrient_key]

        if (
            a["amount"] is None
            or b["amount"] is None
        ):
            continue

        question = (
            f"Compare the recorded {a['name']} "
            f"values for {food_a['food_name']} "
            f"and {food_b['food_name']}. "
            "Which recorded value is higher?"
        )

        if a["amount"] > b["amount"]:
            answer = (
                f"{food_a['food_name']} has the "
                f"higher recorded {a['name']} "
                f"value: {a['amount']:g} {a['unit']}, "
                f"compared with {b['amount']:g} "
                f"{b['unit']} for "
                f"{food_b['food_name']}."
            )

        elif b["amount"] > a["amount"]:
            answer = (
                f"{food_b['food_name']} has the "
                f"higher recorded {b['name']} "
                f"value: {b['amount']:g} {b['unit']}, "
                f"compared with {a['amount']:g} "
                f"{a['unit']} for "
                f"{food_a['food_name']}."
            )

        else:
            answer = (
                f"The recorded {a['name']} "
                f"values are equal at "
                f"{a['amount']:g} {a['unit']}."
            )

        context = (
            "Evidence A:\n"
            + food_context(food_a)
            + "\n\nEvidence B:\n"
            + food_context(food_b)
        )

        tasks.append(
            make_task(
                "multi_food_comparison",
                question,
                context,
                answer,
                [
                    evidence_id(food_a, "A"),
                    evidence_id(food_b, "B"),
                ],
                [
                    food_a["food_id"],
                    food_b["food_id"],
                ],
                "USDA FoodData Central",
                {
                    "nutrient": a["name"],
                    "comparison": True,
                },
            )
        )

    return tasks


def build_evidence_selection_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    shuffled = foods[:]
    rng.shuffle(shuffled)

    tasks = []

    for food in shuffled:
        if len(tasks) >= target:
            break

        if not food["nutrients"]:
            continue

        nutrient = rng.choice(
            food["nutrients"]
        )

        question = (
            "Which evidence record should be used "
            "to answer a question about "
            f"{nutrient['name']} in "
            f"{food['food_name']}?"
        )

        answer = (
            "Use the USDA FoodData Central record "
            f"for {food['food_name']} "
            f"(food ID {food['food_id']}) "
            "because it contains the relevant "
            "nutrient evidence."
        )

        tasks.append(
            make_task(
                "evidence_selection",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
                {
                    "selected_evidence": (
                        evidence_id(food)
                    ),
                    "nutrient": nutrient["name"],
                },
            )
        )

    return tasks


def build_evidence_sufficiency_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    shuffled = foods[:]
    rng.shuffle(shuffled)

    tasks = []

    for food in shuffled:
        if len(tasks) >= target:
            break

        nutrients = nutrient_candidates(food)

        if not nutrients:
            continue

        n = rng.choice(nutrients)

        question = (
            "Is the provided evidence sufficient "
            "to state the recorded "
            f"{n['name']} amount for "
            f"{food['food_name']}?"
        )

        answer = (
            "Yes. The USDA record explicitly "
            f"reports {n['amount']:g} "
            f"{n['unit']} for {n['name']}."
        )

        tasks.append(
            make_task(
                "evidence_sufficiency",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
                {
                    "sufficient": True,
                    "nutrient": n["name"],
                },
            )
        )

    return tasks


def build_rejection_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    shuffled = foods[:]
    rng.shuffle(shuffled)

    tasks = []

    for food in shuffled:
        if len(tasks) >= target:
            break

        nutrients = nutrient_candidates(food)

        if not nutrients:
            continue

        n = rng.choice(nutrients)

        question = (
            "Can the evidence establish that "
            f"{food['food_name']} contains a "
            "nutrient not reported in the "
            "provided record?"
        )

        answer = (
            "No. The provided evidence does not "
            "report that claim, so it should not "
            "be asserted as an "
            "evidence-supported fact."
        )

        tasks.append(
            make_task(
                "evidence_bounded_rejection",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
                {
                    "supported": False,
                    "rejection_reason": (
                        "claim not established by "
                        "provided evidence"
                    ),
                    "reference_nutrient": n["name"],
                },
            )
        )

    return tasks


def build_missing_value_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    # We only use genuinely missing values.
    candidates = []

    for food in foods:
        for n in food["nutrients"]:
            if n["amount"] is None:
                candidates.append(
                    (food, n)
                )

    rng.shuffle(candidates)

    tasks = []

    for food, n in candidates[:target]:
        question = (
            f"What is the reported amount of "
            f"{n['name']} in "
            f"{food['food_name']}?"
        )

        answer = (
            "The provided USDA record does not "
            f"report a usable numeric amount for "
            f"{n['name']}. The answer should "
            "therefore be stated as not reported "
            "rather than inferred."
        )

        tasks.append(
            make_task(
                "missing_value_uncertainty",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
                {
                    "numeric_value_available": False,
                    "nutrient": n["name"],
                },
            )
        )

    return tasks


def build_provenance_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    shuffled = foods[:]
    rng.shuffle(shuffled)

    tasks = []

    for food in shuffled:
        if len(tasks) >= target:
            break

        question = (
            "What is the provenance of the "
            "evidence used for "
            f"{food['food_name']}?"
        )

        answer = (
            f"The evidence comes from "
            f"{food['source']}, identified by "
            f"food ID {food['food_id']}."
        )

        tasks.append(
            make_task(
                "provenance_reasoning",
                question,
                food_context(food),
                answer,
                [evidence_id(food)],
                [food["food_id"]],
                food["source"],
            )
        )

    return tasks


def build_source_aware_tasks(
    foods: list[dict],
    target: int,
    rng: random.Random,
) -> list[dict]:

    by_source = defaultdict(list)

    for food in foods:
        by_source[food["source"]].append(food)

    sources = list(by_source)

    if len(sources) < 2:
        return []

    tasks = []

    for source_a, source_b in (
        (
            sources[i],
            sources[j],
        )
        for i in range(len(sources))
        for j in range(
            i + 1,
            len(sources),
        )
    ):

        a_items = by_source[source_a][:]
        b_items = by_source[source_b][:]

        rng.shuffle(a_items)
        rng.shuffle(b_items)

        for food_a, food_b in zip(
            a_items,
            b_items,
        ):
            if len(tasks) >= target:
                return tasks

            question = (
                "Which sources are represented "
                "by the two evidence records?"
            )

            answer = (
                f"Evidence A comes from "
                f"{food_a['source']}; evidence B "
                f"comes from {food_b['source']}."
            )

            context = (
                "Evidence A:\n"
                + food_context(food_a)
                + "\n\nEvidence B:\n"
                + food_context(food_b)
            )

            tasks.append(
                make_task(
                    "source_aware_comparison",
                    question,
                    context,
                    answer,
                    [
                        evidence_id(food_a, "A"),
                        evidence_id(food_b, "B"),
                    ],
                    [
                        food_a["food_id"],
                        food_b["food_id"],
                    ],
                    "USDA FoodData Central",
                    {
                        "source_a": food_a["source"],
                        "source_b": food_b["source"],
                    },
                )
            )

    return tasks


def split_by_food(
    tasks: list[dict],
    train_ratio: float = 0.80,
    validation_ratio: float = 0.10,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Strict food-level split.

    Tasks are connected through shared food IDs.

    Example:

        Task 1: A
        Task 2: A + B
        Task 3: B + C

    A, B and C form one connected component and therefore
    must all remain in one split.

    This prevents indirect food-level leakage.
    """

    if not tasks:
        return [], [], []

    parent: dict[str, str] = {}
    rank: dict[str, int] = {}

    def make_set(item: str) -> None:
        if item not in parent:
            parent[item] = item
            rank[item] = 0

    def find(item: str) -> str:
        root = item

        while parent[root] != root:
            root = parent[root]

        while parent[item] != item:
            next_item = parent[item]
            parent[item] = root
            item = next_item

        return root

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if rank[root_a] < rank[root_b]:
            parent[root_a] = root_b

        elif rank[root_a] > rank[root_b]:
            parent[root_b] = root_a

        else:
            parent[root_b] = root_a
            rank[root_a] += 1

    task_food_ids: dict[str, tuple[str, ...]] = {}

    for task in tasks:
        task_id = task["task_id"]

        ids = tuple(
            sorted(
                set(
                    str(x)
                    for x in task.get(
                        "food_ids",
                        [],
                    )
                    if x is not None
                )
            )
        )

        if not ids:
            ids = (f"task:{task_id}",)

        task_food_ids[task_id] = ids

        for food_id_value in ids:
            make_set(food_id_value)

        first = ids[0]

        for food_id_value in ids[1:]:
            union(
                first,
                food_id_value,
            )

    components: dict[str, list[str]] = {}

    for food_id_value in parent:
        root = find(food_id_value)

        components.setdefault(
            root,
            [],
        ).append(food_id_value)

    component_tasks: dict[str, list[dict]] = {}

    for task in tasks:
        ids = task_food_ids[
            task["task_id"]
        ]

        root = find(ids[0])

        component_tasks.setdefault(
            root,
            [],
        ).append(task)

    components_with_tasks = []

    for root, component_foods in (
        components.items()
    ):
        component_task_list = (
            component_tasks.get(
                root,
                [],
            )
        )

        components_with_tasks.append(
            (
                len(component_task_list),
                root,
                component_foods,
                component_task_list,
            )
        )

    # Largest components first.
    components_with_tasks.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    total_tasks = len(tasks)

    target_train = (
        total_tasks * train_ratio
    )

    target_validation = (
        total_tasks * validation_ratio
    )

    train: list[dict] = []
    validation: list[dict] = []
    test: list[dict] = []

    # Greedy allocation of indivisible components.
    #
    # Exact 80/10/10 is not guaranteed because components cannot
    # be split. Leakage prevention takes priority.
    for (
        component_size,
        _root,
        _component_foods,
        component_task_list,
    ) in components_with_tasks:

        current_train = len(train)
        current_validation = len(
            validation
        )

        if current_train < target_train:
            train.extend(
                component_task_list
            )

        elif current_validation < target_validation:
            validation.extend(
                component_task_list
            )

        else:
            test.extend(
                component_task_list
            )

    # --------------------------------------------------------------
    # Hard internal checks.
    # --------------------------------------------------------------

    train_ids = {
        task["task_id"]
        for task in train
    }

    validation_ids = {
        task["task_id"]
        for task in validation
    }

    test_ids = {
        task["task_id"]
        for task in test
    }

    if train_ids & validation_ids:
        raise RuntimeError(
            "Internal error: "
            "train/validation task overlap."
        )

    if train_ids & test_ids:
        raise RuntimeError(
            "Internal error: "
            "train/test task overlap."
        )

    if validation_ids & test_ids:
        raise RuntimeError(
            "Internal error: "
            "validation/test task overlap."
        )

    original_ids = {
        task["task_id"]
        for task in tasks
    }

    if (
        train_ids
        | validation_ids
        | test_ids
    ) != original_ids:
        raise RuntimeError(
            "Internal error: "
            "tasks were lost during splitting."
        )

    def food_ids_for(
        rows: list[dict],
    ) -> set[str]:
        result = set()

        for row in rows:
            result.update(
                str(x)
                for x in row.get(
                    "food_ids",
                    [],
                )
            )

        return result

    train_foods = food_ids_for(train)
    validation_foods = food_ids_for(
        validation
    )
    test_foods = food_ids_for(test)

    if train_foods & validation_foods:
        raise RuntimeError(
            "Internal error: "
            "food leakage between train "
            "and validation."
        )

    if train_foods & test_foods:
        raise RuntimeError(
            "Internal error: "
            "food leakage between train "
            "and test."
        )

    if validation_foods & test_foods:
        raise RuntimeError(
            "Internal error: "
            "food leakage between validation "
            "and test."
        )

    return (
        train,
        validation,
        test,
    )


def write_jsonl(
    path: Path,
    rows: list[dict],
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:

        for row in rows:
            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )


def load_normalized() -> list[dict]:

    if not NORMALIZED_PATH.exists():
        raise SystemExit(
            "Missing normalized USDA dataset:\n"
            f"{NORMALIZED_PATH}"
        )

    foods = []

    with NORMALIZED_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:

        for line_no, line in enumerate(
            f,
            1,
        ):
            if not line.strip():
                continue

            try:
                record = json.loads(line)

            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"Invalid JSON at line "
                    f"{line_no}: {exc}"
                )

            if isinstance(record, dict):
                foods.append(
                    normalize_record(record)
                )

    return foods


def main() -> None:

    print("=" * 72)
    print(
        "FOODINSIGHT-LM V0.3 DATASET ENRICHMENT"
    )
    print("=" * 72)
    print()

    rng = random.Random(SEED)

    foods = load_normalized()

    if not foods:
        raise SystemExit(
            "No normalized USDA foods found."
        )

    print(
        f"Normalized foods loaded: "
        f"{len(foods):,}"
    )
    print()

    builders = [
        (
            "direct_nutrient_qa",
            build_direct_nutrient_tasks,
        ),
        (
            "numerical_reasoning",
            build_numerical_tasks,
        ),
        (
            "portion_reasoning",
            build_portion_tasks,
        ),
        (
            "multi_food_comparison",
            build_multi_food_comparison_tasks,
        ),
        (
            "evidence_selection",
            build_evidence_selection_tasks,
        ),
        (
            "evidence_sufficiency",
            build_evidence_sufficiency_tasks,
        ),
        (
            "evidence_bounded_rejection",
            build_rejection_tasks,
        ),
        (
            "missing_value_uncertainty",
            build_missing_value_tasks,
        ),
        (
            "provenance_reasoning",
            build_provenance_tasks,
        ),
        (
            "source_aware_comparison",
            build_source_aware_tasks,
        ),
    ]

    tasks_by_family = {}

    for family, builder in builders:

        print(
            f"Building {family}..."
        )

        tasks = builder(
            foods,
            TARGETS[family],
            rng,
        )

        tasks_by_family[family] = tasks

        print(
            f"  generated: "
            f"{len(tasks):,} / target "
            f"{TARGETS[family]:,}"
        )

    seen = set()
    tasks = []

    for family in tasks_by_family:

        for task in tasks_by_family[
            family
        ]:

            if task["task_id"] in seen:
                continue

            seen.add(task["task_id"])
            tasks.append(task)

    rng.shuffle(tasks)

    print()
    print(
        f"Unique V0.3 tasks: "
        f"{len(tasks):,}"
    )
    print()

    train, validation, test = split_by_food(
        tasks
    )

    print("Leakage-safe split:")
    print(
        f"  Train:      {len(train):,}"
    )
    print(
        f"  Validation: {len(validation):,}"
    )
    print(
        f"  Test:       {len(test):,}"
    )
    print()

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_path = (
        OUT_DIR
        / "foodinsight_usda_v0_3.jsonl"
    )

    train_path = (
        OUT_DIR
        / "foodinsight_usda_v0_3_train.jsonl"
    )

    validation_path = (
        OUT_DIR
        / "foodinsight_usda_v0_3_validation.jsonl"
    )

    test_path = (
        OUT_DIR
        / "foodinsight_usda_v0_3_test.jsonl"
    )

    metadata_path = (
        OUT_DIR
        / "foodinsight_usda_v0_3_metadata.json"
    )

    write_jsonl(
        all_path,
        tasks,
    )

    write_jsonl(
        train_path,
        train,
    )

    write_jsonl(
        validation_path,
        validation,
    )

    write_jsonl(
        test_path,
        test,
    )

    family_counts = Counter(
        task["task_family"]
        for task in tasks
    )

    source_counts = Counter(
        task["source"]
        for task in tasks
    )

    metadata = {
        "dataset_version": "v0.3",
        "builder_seed": SEED,
        "source_normalized_dataset": str(
            NORMALIZED_PATH.relative_to(
                ROOT
            )
        ),
        "v02_baseline_preserved": (
            V02_DIR.exists()
        ),
        "normalized_food_count": len(
            foods
        ),
        "total_tasks": len(tasks),
        "train_tasks": len(train),
        "validation_tasks": len(
            validation
        ),
        "test_tasks": len(test),
        "task_family_counts": dict(
            sorted(
                family_counts.items()
            )
        ),
        "source_counts": dict(
            sorted(
                source_counts.items()
            )
        ),
        "targets": TARGETS,
        "split_strategy": (
            "strict deterministic "
            "food-connected-component "
            "split; tasks sharing or "
            "connecting food IDs remain "
            "in the same split"
        ),
        "task_families": [
            "direct_nutrient_qa",
            "numerical_reasoning",
            "portion_reasoning",
            "multi_food_comparison",
            "evidence_selection",
            "evidence_sufficiency",
            "evidence_bounded_rejection",
            "missing_value_uncertainty",
            "provenance_reasoning",
            "source_aware_comparison",
        ],
        "research_notes": [
            "V0.2 is preserved and not overwritten.",
            "Tasks are derived from normalized USDA records.",
            "No fabricated nutrient values are introduced.",
            "Numerical reasoning explicitly states the per-100-g basis.",
            "Unsupported-claim tasks are framed as evidence-bounded rejection.",
            "Conflict examples are not fabricated from USDA records.",
            "Food-level leakage is prevented through connected-component splitting.",
            "V0.3 is an enrichment experiment and requires validation before training.",
        ],
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 72)
    print(
        "FOODINSIGHT-LM V0.3 DATASET BUILDER: "
        "COMPLETE"
    )
    print("=" * 72)
    print()

    print("Task distribution:")

    for family, count in (
        family_counts.most_common()
    ):

        percentage = (
            count
            / len(tasks)
            * 100
        )

        print(
            f"  {family:<32}"
            f"{count:>8,} "
            f"({percentage:6.2f}%)"
        )

    print()
    print("Outputs:")

    for path in (
        all_path,
        train_path,
        validation_path,
        test_path,
        metadata_path,
    ):
        print(f"  {path}")

    print()
    print(
        "V0.2 remains untouched."
    )

    print(
        "Run validate_dataset_v03.py "
        "before training."
    )


if __name__ == "__main__":
    main()