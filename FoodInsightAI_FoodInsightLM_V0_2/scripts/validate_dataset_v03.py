from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = (
    ROOT
    / "research"
    / "dataset"
    / "foodinsight_lm"
    / "v0_3"
)

FILES = {
    "all": DATASET_DIR / "foodinsight_usda_v0_3.jsonl",
    "train": DATASET_DIR / "foodinsight_usda_v0_3_train.jsonl",
    "validation": DATASET_DIR / "foodinsight_usda_v0_3_validation.jsonl",
    "test": DATASET_DIR / "foodinsight_usda_v0_3_test.jsonl",
    "metadata": DATASET_DIR / "foodinsight_usda_v0_3_metadata.json",
}

EXPECTED_FAMILIES = {
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
}


def fail(message: str) -> None:
    raise SystemExit(
        "\n"
        + "=" * 72
        + "\nFOODINSIGHT-LM V0.3 DATASET VALIDATION: FAILED\n"
        + "=" * 72
        + f"\n{message}\n"
    )


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"Missing file:\n{path}")

    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(
                    f"Invalid JSON in {path.name}, "
                    f"line {line_no}: {exc}"
                )

            if not isinstance(row, dict):
                fail(
                    f"{path.name}, line {line_no}: "
                    "record is not a JSON object"
                )

            rows.append(row)

    return rows


def require_string(row: dict, key: str, task_id: str) -> None:
    value = row.get(key)

    if not isinstance(value, str) or not value.strip():
        fail(
            f"{task_id}: '{key}' must be a non-empty string"
        )


def require_list(row: dict, key: str, task_id: str) -> None:
    value = row.get(key)

    if not isinstance(value, list):
        fail(
            f"{task_id}: '{key}' must be a list"
        )


def check_numbers(value, location: str, task_id: str) -> None:
    if isinstance(value, float):
        if not math.isfinite(value):
            fail(
                f"{task_id}: non-finite numeric value "
                f"at {location}"
            )
        return

    if isinstance(value, dict):
        for key, child in value.items():
            check_numbers(
                child,
                f"{location}.{key}",
                task_id,
            )
        return

    if isinstance(value, list):
        for index, child in enumerate(value):
            check_numbers(
                child,
                f"{location}[{index}]",
                task_id,
            )


def extract_food_ids(row: dict) -> set[str]:
    ids: set[str] = set()

    for key in (
        "food_id",
        "fdc_id",
        "food_fdc_id",
    ):
        value = row.get(key)

        if value is not None:
            ids.add(str(value))

    for key in (
        "food_ids",
        "fdc_ids",
    ):
        value = row.get(key)

        if isinstance(value, list):
            for item in value:
                if item is not None:
                    ids.add(str(item))

    return ids


def extract_evidence_ids(row: dict) -> set[str]:
    result: set[str] = set()

    value = row.get("evidence_ids")

    if isinstance(value, list):
        for item in value:
            if item is not None:
                result.add(str(item))

    claims = row.get("claims")

    if isinstance(claims, list):
        for claim in claims:
            if not isinstance(claim, dict):
                continue

            ids = claim.get("evidence_ids")

            if isinstance(ids, list):
                for item in ids:
                    if item is not None:
                        result.add(str(item))

    return result


def validate_records(
    rows: list[dict],
    split_name: str,
) -> tuple[set[str], set[str], Counter]:

    task_ids: set[str] = set()
    food_ids: set[str] = set()
    evidence_ids: set[str] = set()
    families = Counter()

    for index, row in enumerate(rows, 1):

        task_id = row.get("task_id")

        if not isinstance(task_id, str) or not task_id.strip():
            fail(
                f"{split_name}[{index}]: missing task_id"
            )

        if task_id in task_ids:
            fail(
                f"{split_name}: duplicate task_id: {task_id}"
            )

        task_ids.add(task_id)

        # Required fields.
        for field in (
            "task_family",
            "question",
            "context",
            "answer",
            "dataset_version",
            "source",
        ):
            require_string(row, field, task_id)

        require_list(
            row,
            "evidence_ids",
            task_id,
        )

        require_list(
            row,
            "food_ids",
            task_id,
        )

        require_list(
            row,
            "claims",
            task_id,
        )

        # Version check.
        if row["dataset_version"] != "v0.3":
            fail(
                f"{task_id}: dataset_version is "
                f"{row['dataset_version']!r}, expected 'v0.3'"
            )

        # Task family.
        family = row["task_family"]

        if family not in EXPECTED_FAMILIES:
            fail(
                f"{task_id}: unknown task family "
                f"{family!r}"
            )

        families[family] += 1

        # Food IDs.
        row_food_ids = extract_food_ids(row)

        if not row_food_ids:
            fail(
                f"{task_id}: no food IDs found"
            )

        food_ids.update(row_food_ids)

        # Evidence IDs.
        row_evidence_ids = extract_evidence_ids(row)

        if not row_evidence_ids:
            fail(
                f"{task_id}: no evidence IDs found"
            )

        evidence_ids.update(row_evidence_ids)

        # Evidence IDs should be non-empty.
        for evidence_id in row_evidence_ids:
            if not evidence_id.strip():
                fail(
                    f"{task_id}: empty evidence ID"
                )

        # Claims.
        for claim_index, claim in enumerate(
            row["claims"]
        ):
            if not isinstance(claim, dict):
                fail(
                    f"{task_id}: claim {claim_index} "
                    "is not an object"
                )

            claim_text = claim.get("claim")

            if (
                not isinstance(claim_text, str)
                or not claim_text.strip()
            ):
                fail(
                    f"{task_id}: claim {claim_index} "
                    "has empty claim text"
                )

            claim_evidence = claim.get(
                "evidence_ids"
            )

            if not isinstance(claim_evidence, list):
                fail(
                    f"{task_id}: claim {claim_index} "
                    "has invalid evidence_ids"
                )

        # Recursive numerical safety.
        check_numbers(
            row,
            "record",
            task_id,
        )

    print(
        f"[OK] {split_name}: "
        f"{len(rows):,} records"
    )

    return task_ids, food_ids, families


def check_split_overlap(
    name_a: str,
    ids_a: set[str],
    name_b: str,
    ids_b: set[str],
) -> None:

    overlap = ids_a & ids_b

    if overlap:
        sample = sorted(overlap)[:10]

        fail(
            f"{name_a}/{name_b} task-ID overlap: "
            f"{len(overlap):,}\n"
            f"Examples: {sample}"
        )

    print(
        f"[OK] No task-ID overlap: "
        f"{name_a} ↔ {name_b}"
    )


def check_food_overlap(
    name_a: str,
    ids_a: set[str],
    name_b: str,
    ids_b: set[str],
) -> None:

    overlap = ids_a & ids_b

    if overlap:
        sample = sorted(overlap)[:15]

        fail(
            f"FOOD-LEVEL DATA LEAKAGE detected: "
            f"{name_a} ↔ {name_b}\n"
            f"Shared food IDs: {len(overlap):,}\n"
            f"Examples: {sample}"
        )

    print(
        f"[OK] No food-ID overlap: "
        f"{name_a} ↔ {name_b}"
    )


def main() -> None:

    print("=" * 72)
    print("FOODINSIGHT-LM V0.3 DATASET VALIDATOR")
    print("=" * 72)
    print()

    print("Dataset directory:")
    print(f"  {DATASET_DIR}")
    print()

    # --------------------------------------------------------------
    # Files
    # --------------------------------------------------------------

    for name, path in FILES.items():

        if not path.exists():
            fail(
                f"Missing {name} file:\n{path}"
            )

        print(
            f"[OK] {name}: {path.name}"
        )

    print()

    # --------------------------------------------------------------
    # Load
    # --------------------------------------------------------------

    all_rows = load_jsonl(FILES["all"])
    train_rows = load_jsonl(FILES["train"])
    validation_rows = load_jsonl(
        FILES["validation"]
    )
    test_rows = load_jsonl(FILES["test"])

    print("Loaded:")
    print(f"  All:        {len(all_rows):,}")
    print(f"  Train:      {len(train_rows):,}")
    print(
        f"  Validation: {len(validation_rows):,}"
    )
    print(f"  Test:       {len(test_rows):,}")
    print()

    if not all_rows:
        fail("All dataset is empty")

    if not train_rows:
        fail("Training dataset is empty")

    if not validation_rows:
        fail("Validation dataset is empty")

    if not test_rows:
        fail("Test dataset is empty")

    # --------------------------------------------------------------
    # Metadata
    # --------------------------------------------------------------

    try:
        metadata = json.loads(
            FILES["metadata"].read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        fail(
            f"Invalid metadata JSON: {exc}"
        )

    if not isinstance(metadata, dict):
        fail("Metadata is not an object")

    print("[OK] Metadata JSON")
    print()

    # --------------------------------------------------------------
    # Validate records
    # --------------------------------------------------------------

    print("Validating records...")
    print()

    (
        all_task_ids,
        all_food_ids,
        all_families,
    ) = validate_records(
        all_rows,
        "all",
    )

    (
        train_task_ids,
        train_food_ids,
        train_families,
    ) = validate_records(
        train_rows,
        "train",
    )

    (
        validation_task_ids,
        validation_food_ids,
        validation_families,
    ) = validate_records(
        validation_rows,
        "validation",
    )

    (
        test_task_ids,
        test_food_ids,
        test_families,
    ) = validate_records(
        test_rows,
        "test",
    )

    # --------------------------------------------------------------
    # Task isolation
    # --------------------------------------------------------------

    print()
    print("Checking task-ID isolation...")

    check_split_overlap(
        "train",
        train_task_ids,
        "validation",
        validation_task_ids,
    )

    check_split_overlap(
        "train",
        train_task_ids,
        "test",
        test_task_ids,
    )

    check_split_overlap(
        "validation",
        validation_task_ids,
        "test",
        test_task_ids,
    )

    # --------------------------------------------------------------
    # Task coverage
    # --------------------------------------------------------------

    print()
    print("Checking task coverage...")

    split_union = (
        train_task_ids
        | validation_task_ids
        | test_task_ids
    )

    if split_union != all_task_ids:

        missing = all_task_ids - split_union
        extra = split_union - all_task_ids

        if missing:
            fail(
                "Tasks present in all dataset but absent "
                f"from splits: {list(missing)[:10]}"
            )

        if extra:
            fail(
                "Tasks present in splits but absent "
                f"from all dataset: {list(extra)[:10]}"
            )

    print(
        "[OK] Train + validation + test "
        "cover all tasks"
    )

    # --------------------------------------------------------------
    # FOOD-LEVEL LEAKAGE
    # --------------------------------------------------------------

    print()
    print(
        "Checking FOOD-LEVEL split isolation..."
    )

    check_food_overlap(
        "train",
        train_food_ids,
        "validation",
        validation_food_ids,
    )

    check_food_overlap(
        "train",
        train_food_ids,
        "test",
        test_food_ids,
    )

    check_food_overlap(
        "validation",
        validation_food_ids,
        "test",
        test_food_ids,
    )

    # --------------------------------------------------------------
    # Family distribution
    # --------------------------------------------------------------

    print()
    print("Task-family distribution:")

    for name, rows, families in (
        (
            "ALL",
            all_rows,
            all_families,
        ),
        (
            "TRAIN",
            train_rows,
            train_families,
        ),
        (
            "VALIDATION",
            validation_rows,
            validation_families,
        ),
        (
            "TEST",
            test_rows,
            test_families,
        ),
    ):

        print()
        print(f"{name}:")

        for family, count in (
            families.most_common()
        ):
            percentage = (
                count
                / len(rows)
                * 100
            )

            print(
                f"  {family:<32}"
                f"{count:>8,} "
                f"({percentage:6.2f}%)"
            )

    # --------------------------------------------------------------
    # Family presence / quality gates
    # --------------------------------------------------------------

    print()
    print(
        "Checking task-family coverage..."
    )

    missing_families = (
        EXPECTED_FAMILIES
        - set(all_families)
    )

    if missing_families:
        print(
            "[WARNING] Task families with zero "
            "examples:"
        )

        for family in sorted(
            missing_families
        ):
            print(f"  - {family}")

    else:
        print(
            "[OK] All expected task families "
            "are represented"
        )

    # A family with zero examples is not a structural
    # failure because the underlying USDA data may genuinely
    # not support that task type. It is reported explicitly.

    # --------------------------------------------------------------
    # Metadata consistency
    # --------------------------------------------------------------

    print()
    print(
        "Checking metadata consistency..."
    )

    metadata_expected = {
        "total_tasks": len(all_rows),
        "train_tasks": len(train_rows),
        "validation_tasks": len(
            validation_rows
        ),
        "test_tasks": len(test_rows),
        "normalized_food_count": metadata.get(
            "normalized_food_count"
        ),
    }

    for key in (
        "total_tasks",
        "train_tasks",
        "validation_tasks",
        "test_tasks",
    ):

        expected = metadata_expected[key]
        actual = metadata.get(key)

        if actual is None:
            fail(
                f"Metadata missing required field: "
                f"{key}"
            )

        if int(actual) != expected:
            fail(
                f"Metadata mismatch for {key}: "
                f"metadata={actual}, "
                f"actual={expected}"
            )

        print(
            f"[OK] {key}: {expected:,}"
        )

    if metadata.get(
        "dataset_version"
    ) != "v0.3":

        fail(
            "Metadata dataset_version is not 'v0.3'"
        )

    print(
        "[OK] dataset_version: v0.3"
    )

    # --------------------------------------------------------------
    # Task ID namespace
    # --------------------------------------------------------------

    print()
    print(
        "Checking V0.3 task-ID namespace..."
    )

    bad_ids = [
        task_id
        for task_id in all_task_ids
        if not task_id.startswith("v03_")
    ]

    if bad_ids:
        fail(
            "Tasks without v03_ namespace: "
            f"{bad_ids[:10]}"
        )

    print(
        "[OK] All task IDs use v03_ namespace"
    )

    # --------------------------------------------------------------
    # Food-ID sanity
    # --------------------------------------------------------------

    print()
    print(
        "Food identity statistics:"
    )

    print(
        f"  All unique foods: "
        f"{len(all_food_ids):,}"
    )

    print(
        f"  Train unique foods: "
        f"{len(train_food_ids):,}"
    )

    print(
        f"  Validation unique foods: "
        f"{len(validation_food_ids):,}"
    )

    print(
        f"  Test unique foods: "
        f"{len(test_food_ids):,}"
    )

    # --------------------------------------------------------------
    # Final
    # --------------------------------------------------------------

    print()
    print("=" * 72)
    print(
        "FOODINSIGHT-LM V0.3 DATASET VALIDATION: PASSED"
    )
    print("=" * 72)
    print()

    print(
        f"Total tasks:       {len(all_rows):,}"
    )
    print(
        f"Train:             {len(train_rows):,}"
    )
    print(
        f"Validation:        {len(validation_rows):,}"
    )
    print(
        f"Test:              {len(test_rows):,}"
    )
    print()
    print(
        "JSON integrity:     PASSED"
    )
    print(
        "Required fields:   PASSED"
    )
    print(
        "Task isolation:    PASSED"
    )
    print(
        "Food isolation:    PASSED"
    )
    print(
        "Evidence fields:   PASSED"
    )
    print(
        "Numeric safety:    PASSED"
    )
    print(
        "Metadata:          PASSED"
    )
    print()
    print(
        "V0.3 is structurally ready for "
        "research evaluation."
    )
    print()
    print(
        "IMPORTANT: Structural validation does "
        "not establish factual correctness, "
        "scientific validity, or model-training "
        "quality."
    )
    print()


if __name__ == "__main__":
    main()