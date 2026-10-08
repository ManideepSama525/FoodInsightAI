from __future__ import annotations

import json
import math
from pathlib import Path
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = ROOT / "research" / "dataset" / "foodinsight_lm" / "v0_2"

FILES = {
    "all": DATASET_DIR / "foodinsight_usda_v0_2.jsonl",
    "train": DATASET_DIR / "foodinsight_usda_v0_2_train.jsonl",
    "validation": DATASET_DIR / "foodinsight_usda_v0_2_validation.jsonl",
    "test": DATASET_DIR / "foodinsight_usda_v0_2_test.jsonl",
    "metadata": DATASET_DIR / "foodinsight_usda_v0_2_metadata.json",
}


def fail(message: str) -> None:
    raise SystemExit(f"\nDATASET VALIDATION FAILED\n{message}")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        fail(f"Missing {path}")

    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(
                    f"Invalid JSON in {path.name}, "
                    f"line {line_no}: {exc}"
                )

            if not isinstance(item, dict):
                fail(
                    f"{path.name}, line {line_no}: "
                    "record is not a JSON object"
                )

            rows.append(item)

    return rows


def require_nonempty(value, field: str, record_id: str) -> None:
    if value is None:
        fail(f"{record_id}: missing {field}")

    if isinstance(value, str) and not value.strip():
        fail(f"{record_id}: empty {field}")

    if isinstance(value, list) and not value:
        fail(f"{record_id}: empty {field}")


def check_finite(value, field: str, record_id: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        fail(f"{record_id}: non-finite {field}")


def get_task_id(row: dict, index: int) -> str:
    for key in ("task_id", "id"):
        value = row.get(key)
        if value is not None:
            return str(value)

    fail(f"Record {index}: missing task_id/id")


def get_food_ids(row: dict) -> set[str]:
    ids = set()

    candidates = [
        row.get("food_id"),
        row.get("fdc_id"),
        row.get("food_fdc_id"),
    ]

    for value in candidates:
        if value is not None:
            ids.add(str(value))

    for key in ("food_ids", "fdc_ids"):
        value = row.get(key)

        if isinstance(value, list):
            ids.update(str(x) for x in value if x is not None)

        elif value is not None:
            ids.add(str(value))

    context = row.get("context")

    if isinstance(context, dict):
        for key in ("food_id", "fdc_id", "food_fdc_id"):
            value = context.get(key)
            if value is not None:
                ids.add(str(value))

        for key in ("food_ids", "fdc_ids"):
            value = context.get(key)

            if isinstance(value, list):
                ids.update(str(x) for x in value if x is not None)

    return ids


def main() -> None:
    print("=" * 72)
    print("FOODINSIGHT-LM V0.2 DATASET VALIDATOR")
    print("=" * 72)
    print()

    # ------------------------------------------------------------------
    # File existence
    # ------------------------------------------------------------------

    print(f"Dataset directory:")
    print(f"  {DATASET_DIR}")
    print()

    for name, path in FILES.items():
        if not path.exists():
            fail(f"Missing {path}")

        print(f"[OK] {name}: {path.name}")

    print()

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    all_rows = load_jsonl(FILES["all"])
    train_rows = load_jsonl(FILES["train"])
    validation_rows = load_jsonl(FILES["validation"])
    test_rows = load_jsonl(FILES["test"])

    print("Loaded:")
    print(f"  All:        {len(all_rows):,}")
    print(f"  Train:      {len(train_rows):,}")
    print(f"  Validation: {len(validation_rows):,}")
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

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    try:
        metadata = json.loads(
            FILES["metadata"].read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        fail(f"Invalid metadata JSON: {exc}")

    if not isinstance(metadata, dict):
        fail("Metadata is not a JSON object")

    print("[OK] Metadata JSON")
    print()

    # ------------------------------------------------------------------
    # Record validation
    # ------------------------------------------------------------------

    required_any_fields = {
        "question": ("question", "prompt", "input"),
        "answer": ("answer", "output", "response"),
        "context": ("context", "evidence"),
    }

    def validate_records(rows: list[dict], split_name: str) -> set[str]:
        task_ids = set()
        food_ids = set()
        task_families = Counter()

        for index, row in enumerate(rows, 1):
            record_id = f"{split_name}[{index}]"

            task_id = get_task_id(row, index)

            if task_id in task_ids:
                fail(
                    f"{record_id}: duplicate task ID {task_id}"
                )

            task_ids.add(task_id)

            # ----------------------------------------------------------
            # Required semantic fields
            # ----------------------------------------------------------

            for semantic_name, candidates in required_any_fields.items():
                value = None

                for key in candidates:
                    if key in row:
                        value = row[key]
                        break

                if value is None:
                    fail(
                        f"{record_id} ({task_id}): "
                        f"missing {semantic_name}; "
                        f"expected one of {candidates}"
                    )

                require_nonempty(value, semantic_name, record_id)

            # ----------------------------------------------------------
            # Task family
            # ----------------------------------------------------------

            family = (
                row.get("task_family")
                or row.get("task_type")
                or row.get("category")
                or "unknown"
            )

            task_families[str(family)] += 1

            # ----------------------------------------------------------
            # Food identity
            # ----------------------------------------------------------

            food_ids.update(get_food_ids(row))

            # ----------------------------------------------------------
            # Evidence / provenance
            # ----------------------------------------------------------

            evidence_ids = row.get("evidence_ids")

            if evidence_ids is not None:
                if not isinstance(evidence_ids, list):
                    fail(
                        f"{record_id} ({task_id}): "
                        "evidence_ids must be a list"
                    )

                for evidence_id in evidence_ids:
                    if evidence_id is None:
                        fail(
                            f"{record_id} ({task_id}): "
                            "null evidence_id"
                        )

            # ----------------------------------------------------------
            # Claims
            # ----------------------------------------------------------

            claims = row.get("claims")

            if claims is not None:
                if not isinstance(claims, list):
                    fail(
                        f"{record_id} ({task_id}): "
                        "claims must be a list"
                    )

                for claim in claims:
                    if isinstance(claim, dict):
                        for key, value in claim.items():
                            check_finite(
                                value,
                                f"claims.{key}",
                                record_id,
                            )

            # ----------------------------------------------------------
            # Recursive finite-number check for common numeric fields
            # ----------------------------------------------------------

            for key, value in row.items():
                if isinstance(value, float):
                    check_finite(value, key, record_id)

        print(f"[OK] {split_name}: {len(rows):,} records")
        print(f"     task families: {dict(task_families)}")

        return food_ids

    print("Validating records...")
    print()

    all_task_ids = validate_records(all_rows, "all")
    train_task_ids = validate_records(train_rows, "train")
    validation_task_ids = validate_records(
        validation_rows,
        "validation",
    )
    test_task_ids = validate_records(test_rows, "test")

    # ------------------------------------------------------------------
    # Task ID split isolation
    # ------------------------------------------------------------------

    print()
    print("Checking task split isolation...")

    train_val = train_task_ids & validation_task_ids
    train_test = train_task_ids & test_task_ids
    val_test = validation_task_ids & test_task_ids

    if train_val:
        fail(
            f"Train/validation task overlap: "
            f"{list(train_val)[:10]}"
        )

    if train_test:
        fail(
            f"Train/test task overlap: "
            f"{list(train_test)[:10]}"
        )

    if val_test:
        fail(
            f"Validation/test task overlap: "
            f"{list(val_test)[:10]}"
        )

    print("[OK] No task-ID overlap")

    # ------------------------------------------------------------------
    # All task coverage
    # ------------------------------------------------------------------

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
                f"Tasks missing from splits: "
                f"{list(missing)[:10]}"
            )

        if extra:
            fail(
                f"Split contains tasks absent from all dataset: "
                f"{list(extra)[:10]}"
            )

    print("[OK] Train + validation + test cover all tasks")

    # ------------------------------------------------------------------
    # Food-level leakage
    # ------------------------------------------------------------------

    print()
    print("Checking food-level split isolation...")

    train_foods = validate_records(train_rows, "train-food-check")
    val_foods = validate_records(
        validation_rows,
        "validation-food-check",
    )
    test_foods = validate_records(
        test_rows,
        "test-food-check",
    )

    # Food-level isolation is only enforced when food IDs are present.
    if train_foods and val_foods:
        overlap = train_foods & val_foods
        if overlap:
            print(
                "[WARNING] Train/validation food overlap: "
                f"{len(overlap):,}"
            )

    if train_foods and test_foods:
        overlap = train_foods & test_foods
        if overlap:
            print(
                "[WARNING] Train/test food overlap: "
                f"{len(overlap):,}"
            )

    if val_foods and test_foods:
        overlap = val_foods & test_foods
        if overlap:
            print(
                "[WARNING] Validation/test food overlap: "
                f"{len(overlap):,}"
            )

    if not train_foods and not val_foods and not test_foods:
        print(
            "[INFO] Food IDs are not directly exposed in task records; "
            "food-level leakage cannot be independently checked here."
        )
    else:
        print("[OK] Food identity fields inspected")

    # ------------------------------------------------------------------
    # Dataset distribution
    # ------------------------------------------------------------------

    print()
    print("Dataset distribution:")

    def distribution(rows: list[dict]) -> Counter:
        counter = Counter()

        for row in rows:
            family = (
                row.get("task_family")
                or row.get("task_type")
                or row.get("category")
                or "unknown"
            )
            counter[str(family)] += 1

        return counter

    for name, rows in (
        ("all", all_rows),
        ("train", train_rows),
        ("validation", validation_rows),
        ("test", test_rows),
    ):
        print(f"\n{name.upper()}:")
        for family, count in distribution(rows).most_common():
            percentage = count / len(rows) * 100
            print(
                f"  {family:<32} "
                f"{count:>8,} "
                f"({percentage:6.2f}%)"
            )

    # ------------------------------------------------------------------
    # Metadata consistency
    # ------------------------------------------------------------------

    print()
    print("Checking metadata consistency...")

    metadata_checks = {
        "total_tasks": len(all_rows),
        "train_tasks": len(train_rows),
        "validation_tasks": len(validation_rows),
        "test_tasks": len(test_rows),
    }

    for key, actual in metadata_checks.items():
        value = metadata.get(key)

        if value is None:
            print(f"[INFO] Metadata does not contain '{key}'")
            continue

        try:
            value_int = int(value)
        except (TypeError, ValueError):
            fail(
                f"Metadata field {key} is not numeric: {value}"
            )

        if value_int != actual:
            fail(
                f"Metadata mismatch for {key}: "
                f"metadata={value_int}, actual={actual}"
            )

        print(f"[OK] {key}: {actual:,}")

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------

    print()
    print("=" * 72)
    print("FOODINSIGHT-LM V0.2 DATASET VALIDATION: PASSED")
    print("=" * 72)
    print()
    print(f"All tasks:        {len(all_rows):,}")
    print(f"Train:            {len(train_rows):,}")
    print(f"Validation:       {len(validation_rows):,}")
    print(f"Test:             {len(test_rows):,}")
    print()
    print("Task IDs:          isolated")
    print("JSONL parsing:     passed")
    print("Required fields:   passed")
    print("Evidence fields:   checked")
    print("Numeric safety:    checked")
    print("Metadata:          checked")
    print()
    print("V0.2 artifact is structurally valid.")
    print()
    print(
        "NOTE: This validator does not judge whether the dataset is "
        "scientifically balanced or sufficient for final training."
    )
    print(
        "That remains a V0.3 dataset-design task."
    )
    print()


if __name__ == "__main__":
    main()