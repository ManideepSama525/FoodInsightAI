from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Prefer the research V0.2 location if it exists. Fall back to V0.1.
CANDIDATES = [
    ROOT / "research/dataset/foodinsight_lm/foodinsight_usda_v0_2.jsonl",
    ROOT / "research/dataset/foodinsight_lm/foodinsight_usda_train.jsonl",
]

OUTPUT_DIR = ROOT / "research/dataset/foodinsight_lm/training_ready"
TRAIN = OUTPUT_DIR / "train.jsonl"
VALIDATION = OUTPUT_DIR / "validation.jsonl"
TEST = OUTPUT_DIR / "test.jsonl"
REPORT = OUTPUT_DIR / "dataset_report.json"

SEED = 20261001
random.seed(SEED)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    source = next((p for p in CANDIDATES if p.exists()), None)
    if source is None:
        raise SystemExit(
            "No dataset found. Expected V0.2 or V0.1 JSONL under "
            "research/dataset/foodinsight_lm/. "
            "Place the dataset there before training."
        )

    rows = read_jsonl(source)
    if not rows:
        raise SystemExit("Dataset is empty.")

    # If explicit split metadata already exists, preserve it.
    if all(row.get("split") in {"train", "validation", "test"} for row in rows):
        train = [r for r in rows if r["split"] == "train"]
        validation = [r for r in rows if r["split"] == "validation"]
        test = [r for r in rows if r["split"] == "test"]
        split_method = "preserved_existing_split"
    else:
        # This fallback is intentionally conservative. Final research training
        # should use food-level split isolation, not task-level random splitting.
        ids = []
        for row in rows:
            key = (
                row.get("food_fdc_id")
                or row.get("fdc_id")
                or row.get("food_id")
                or row.get("source_id")
                or row.get("id")
            )
            ids.append(str(key))

        groups = sorted(set(ids))
        random.shuffle(groups)

        n = len(groups)
        n_train = max(1, int(n * 0.8))
        n_val = max(1, int(n * 0.1))

        train_groups = set(groups[:n_train])
        val_groups = set(groups[n_train:n_train + n_val])
        test_groups = set(groups[n_train + n_val:])

        train = [r for r, gid in zip(rows, ids) if gid in train_groups]
        validation = [r for r, gid in zip(rows, ids) if gid in val_groups]
        test = [r for r, gid in zip(rows, ids) if gid in test_groups]
        split_method = "grouped_fallback_split"

    for row in rows:
        if not row.get("question") or not row.get("answer"):
            raise ValueError(f"Missing question/answer in record: {row.get('id')}")

    write_jsonl(TRAIN, train)
    write_jsonl(VALIDATION, validation)
    write_jsonl(TEST, test)

    report = {
        "source": str(source.relative_to(ROOT)),
        "total": len(rows),
        "train": len(train),
        "validation": len(validation),
        "test": len(test),
        "seed": SEED,
        "split_method": split_method,
        "research_warning": (
            "V0.1 is an experiment artifact. Final research evaluation must "
            "enforce food-level isolation and balanced task families."
        ),
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
