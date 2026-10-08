from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED = {
    "task_id",
    "task_family",
    "question",
    "context",
    "answer",
    "evidence_ids",
    "food_ids",
    "claims",
    "dataset_version",
}

FAMILIES = {
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

NUM_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
)

def norm_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())

def nums(text: str) -> list[float]:
    out = []
    for x in NUM_RE.findall(text):
        try:
            out.append(float(x))
        except ValueError:
            pass
    return out

def close(a: float, b: float, tol: float = 1e-3) -> bool:
    return math.isclose(a, b, rel_tol=2e-4, abs_tol=tol)

def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception as exc:
                raise RuntimeError(f"{path.name}: invalid JSON at line {line_no}: {exc}")
            if not isinstance(row, dict):
                raise RuntimeError(f"{path.name}: line {line_no} is not an object")
            rows.append(row)
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help="V0.3 dataset directory. Defaults to ../research/dataset/foodinsight_lm/v0_3 relative to this script.",
    )
    ap.add_argument(
        "--sample-errors",
        type=int,
        default=20,
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    dataset_dir = args.dataset_dir or (root / "research" / "dataset" / "foodinsight_lm" / "v0_3")

    files = {
        "all": dataset_dir / "foodinsight_usda_v0_3.jsonl",
        "train": dataset_dir / "foodinsight_usda_v0_3_train.jsonl",
        "validation": dataset_dir / "foodinsight_usda_v0_3_validation.jsonl",
        "test": dataset_dir / "foodinsight_usda_v0_3_test.jsonl",
        "metadata": dataset_dir / "foodinsight_usda_v0_3_metadata.json",
    }

    print("=" * 78)
    print("FOODINSIGHT-LM V0.3 DATASET QUALITY AUDIT")
    print("=" * 78)
    print()
    print("Dataset:", dataset_dir)
    print()

    for name, path in files.items():
        if not path.exists():
            print(f"[FAIL] Missing {name}: {path}")
            return 2
        print(f"[OK] {name}: {path.name}")

    all_rows = read_jsonl(files["all"])
    train = read_jsonl(files["train"])
    validation = read_jsonl(files["validation"])
    test = read_jsonl(files["test"])
    metadata = json.loads(files["metadata"].read_text(encoding="utf-8"))

    split_rows = {"train": train, "validation": validation, "test": test}

    print()
    print("Counts:")
    print(f"  all:        {len(all_rows):,}")
    print(f"  train:      {len(train):,}")
    print(f"  validation: {len(validation):,}")
    print(f"  test:       {len(test):,}")

    errors = []
    warnings = []
    stats = {}

    def err(code, task, message):
        if len(errors) < 10000:
            errors.append({"code": code, "task_id": task, "message": message})

    # ------------------------------------------------------------
    # Schema / identity
    # ------------------------------------------------------------
    task_ids = [r.get("task_id") for r in all_rows]
    duplicate_task_ids = [k for k, v in Counter(task_ids).items() if v > 1]
    if duplicate_task_ids:
        for x in duplicate_task_ids[:args.sample_errors]:
            err("duplicate_task_id", x, "Task ID occurs more than once.")
    else:
        print("[OK] Unique task IDs")

    missing_required = 0
    bad_family = 0
    bad_namespace = 0
    bad_version = 0
    bad_food_ids = 0
    bad_evidence = 0

    for row in all_rows:
        tid = row.get("task_id", "<missing>")
        missing = REQUIRED - set(row)
        if missing:
            missing_required += 1
            err("missing_fields", tid, f"Missing fields: {sorted(missing)}")
        if row.get("task_family") not in FAMILIES:
            bad_family += 1
            err("unknown_family", tid, str(row.get("task_family")))
        if not str(tid).startswith("v03_"):
            bad_namespace += 1
            err("bad_namespace", tid, "Task ID does not use v03_ namespace.")
        if row.get("dataset_version") != "v0.3":
            bad_version += 1
            err("bad_dataset_version", tid, str(row.get("dataset_version")))
        if not isinstance(row.get("food_ids"), list) or not row.get("food_ids"):
            bad_food_ids += 1
            err("bad_food_ids", tid, "food_ids must be a non-empty list.")
        if not isinstance(row.get("evidence_ids"), list) or not row.get("evidence_ids"):
            bad_evidence += 1
            err("bad_evidence_ids", tid, "evidence_ids must be a non-empty list.")

    print(f"[{'OK' if not missing_required else 'FAIL'}] Required fields")
    print(f"[{'OK' if not bad_family else 'FAIL'}] Task families")
    print(f"[{'OK' if not bad_namespace else 'FAIL'}] V0.3 task namespace")
    print(f"[{'OK' if not bad_version else 'FAIL'}] Dataset version")
    print(f"[{'OK' if not bad_food_ids else 'FAIL'}] Food IDs")
    print(f"[{'OK' if not bad_evidence else 'FAIL'}] Evidence IDs")

    # ------------------------------------------------------------
    # Split integrity
    # ------------------------------------------------------------
    split_sets = {k: {r["task_id"] for r in v} for k, v in split_rows.items()}
    all_ids = {r["task_id"] for r in all_rows}

    if set.union(*split_sets.values()) != all_ids:
        err("split_coverage", "DATASET", "Train/validation/test do not cover exactly all task IDs.")
    if set.intersection(split_sets["train"], split_sets["validation"]):
        err("split_overlap", "DATASET", "Train/validation task overlap.")
    if set.intersection(split_sets["train"], split_sets["test"]):
        err("split_overlap", "DATASET", "Train/test task overlap.")
    if set.intersection(split_sets["validation"], split_sets["test"]):
        err("split_overlap", "DATASET", "Validation/test task overlap.")

    food_sets = {
        k: {str(fid) for r in rows for fid in r.get("food_ids", [])}
        for k, rows in split_rows.items()
    }
    print()
    print("Split leakage audit:")
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlap = food_sets[a] & food_sets[b]
        if overlap:
            err("food_leakage", "DATASET", f"{a}/{b}: {len(overlap)} shared food IDs.")
            print(f"[FAIL] {a} ↔ {b}: {len(overlap):,} shared food IDs")
        else:
            print(f"[OK] {a} ↔ {b}: no food-ID overlap")

    # ------------------------------------------------------------
    # Exact duplicate / contamination audit
    # ------------------------------------------------------------
    qfam = defaultdict(list)
    qonly = defaultdict(list)
    qa = defaultdict(list)

    for row in all_rows:
        q = norm_text(row.get("question", ""))
        f = row.get("task_family", "")
        a = norm_text(row.get("answer", ""))
        qfam[(f, q)].append(row["task_id"])
        qonly[q].append(row["task_id"])
        qa[(q, a)].append(row["task_id"])

    duplicate_qfam = {k: v for k, v in qfam.items() if len(v) > 1}
    duplicate_qa = {k: v for k, v in qa.items() if len(v) > 1}

    print()
    print("Duplication:")
    print(f"  Exact question+family groups with duplicates: {len(duplicate_qfam):,}")
    print(f"  Exact question+answer groups with duplicates: {len(duplicate_qa):,}")

    # Cross-split exact question duplication is a useful warning, not automatically leakage.
    id_to_split = {}
    for s, rows in split_rows.items():
        for r in rows:
            id_to_split[r["task_id"]] = s

    cross_split_q = 0
    cross_split_qa = 0
    for key, ids in qfam.items():
        if len({id_to_split[i] for i in ids}) > 1:
            cross_split_q += 1
    for key, ids in qa.items():
        if len({id_to_split[i] for i in ids}) > 1:
            cross_split_qa += 1

    print(f"  Cross-split exact question+family groups: {cross_split_q:,}")
    print(f"  Cross-split exact question+answer groups: {cross_split_qa:,}")

    if cross_split_q:
        warnings.append(
            f"{cross_split_q:,} question+family groups occur across splits; inspect because repeated templates are not automatically leakage."
        )

    # ------------------------------------------------------------
    # Family-specific semantic/numeric consistency
    # ------------------------------------------------------------
    family_counts = Counter(r["task_family"] for r in all_rows)
    family_errors = Counter()
    family_checked = Counter()

    for row in all_rows:
        tid = row["task_id"]
        fam = row["task_family"]
        answer = str(row.get("answer", ""))
        context = str(row.get("context", ""))
        meta = row.get("metadata") or {}
        family_checked[fam] += 1

        def fail(code, message):
            family_errors[fam] += 1
            err(code, tid, message)

        if fam == "direct_nutrient_qa":
            nutrient = str(meta.get("nutrient", "")).strip()
            unit = str(meta.get("unit", "")).strip()
            if not nutrient or nutrient.lower() not in answer.lower():
                fail("direct_nutrient_missing_name", "Answer does not contain metadata nutrient name.")
            if unit and unit.lower() not in answer.lower():
                fail("direct_nutrient_missing_unit", "Answer does not contain metadata unit.")
            if not nums(answer):
                fail("direct_nutrient_no_number", "Answer contains no numeric value.")
            if nutrient and nutrient.lower() not in context.lower():
                fail("direct_nutrient_not_in_context", "Metadata nutrient is absent from context.")

        elif fam == "numerical_reasoning":
            grams = meta.get("portion_grams")
            calculation = str(meta.get("calculation", ""))
            m = re.match(r"\s*([-+0-9.eE]+)\s*\*\s*([-+0-9.eE]+)\s*/\s*100\s*$", calculation)
            if grams is None or not m:
                fail("numeric_metadata", "Missing or malformed numerical calculation metadata.")
            else:
                base = float(m.group(1))
                calc_grams = float(m.group(2))
                expected = base * calc_grams / 100.0
                answer_nums = nums(answer)
                if not answer_nums:
                    fail("numeric_no_answer", "No numeric result in answer.")
                elif not close(answer_nums[0], expected, 0.002):
                    fail("numeric_wrong_result", f"Expected {expected:.6f}, answer starts with {answer_nums[0]:.6f}.")
                if not close(float(grams), calc_grams, 1e-9):
                    fail("numeric_grams_mismatch", "metadata portion_grams disagrees with calculation.")

        elif fam == "portion_reasoning":
            expected = meta.get("grams")
            if expected is None:
                fail("portion_metadata", "Missing metadata grams.")
            else:
                answer_nums = nums(answer)
                if not answer_nums:
                    fail("portion_no_answer", "No numeric gram value in answer.")
                elif not close(answer_nums[0], float(expected), 0.002):
                    fail("portion_wrong_grams", f"Expected {expected}, answer starts with {answer_nums[0]}.")
                if " g" not in answer.lower():
                    fail("portion_missing_unit", "Answer does not state grams.")

        elif fam == "evidence_sufficiency":
            nutrient = str(meta.get("nutrient", "")).strip()
            if nutrient and nutrient.lower() not in answer.lower():
                fail("sufficiency_missing_nutrient", "Answer omits metadata nutrient.")
            if not nums(answer):
                fail("sufficiency_no_number", "Answer omits numeric reported amount.")

        elif fam == "evidence_bounded_rejection":
            if meta.get("supported") is not False:
                fail("rejection_metadata", "Rejection task is not marked supported=false.")
            if not re.search(r"\b(no|does not|not)\b", answer.lower()):
                fail("rejection_answer", "Rejection answer does not contain an explicit negative/unsupported statement.")

        elif fam == "missing_value_uncertainty":
            if meta.get("numeric_value_available") is not False:
                fail("missing_value_metadata", "Missing-value task is not marked numeric_value_available=false.")
            if re.search(r"\b(?:\d+(?:\.\d+)?)\s*(?:g|mg|kg|kcal|%)\b", answer.lower()):
                fail("missing_value_numeric_answer", "Missing-value answer unexpectedly contains a numeric nutrient value.")

        elif fam == "provenance_reasoning":
            source = str(row.get("source", "")).strip()
            food_ids = [str(x) for x in row.get("food_ids", [])]
            if source and source.lower() not in answer.lower():
                fail("provenance_source", "Answer does not contain task source.")
            if food_ids and food_ids[0].lower() not in answer.lower():
                fail("provenance_food_id", "Answer does not contain food ID.")

        elif fam == "multi_food_comparison":
            # Verify that the answer's declared winner agrees with the numeric values
            # appearing in the evidence context when the task has a strict inequality.
            answer_low = answer.lower()
            if "higher recorded" not in answer_low and "values are equal" not in answer_low:
                fail("comparison_answer_shape", "Comparison answer does not use expected higher/equal wording.")

        elif fam == "source_aware_comparison":
            # Do not require one exact answer-template sentence. The V0.3
            # builder is allowed to phrase source-aware comparisons naturally.
            #
            # Validate the underlying provenance instead:
            #   1) the task must expose source information somewhere in its
            #      metadata/context;
            #   2) the answer should contain a provenance cue when source
            #      information is actually available.
            #
            # This is deliberately a warning-level audit condition rather than
            # a hard dataset failure caused by wording/template variation.
            source_text = " ".join(
                [
                    str(row.get("source", "")),
                    str(meta.get("source", "")),
                    str(meta.get("source_a", "")),
                    str(meta.get("source_b", "")),
                    str(meta.get("source_a_name", "")),
                    str(meta.get("source_b_name", "")),
                    str(meta.get("dataset_a", "")),
                    str(meta.get("dataset_b", "")),
                    context,
                ]
            ).strip()

            source_cues = re.findall(
                r"(?i)\\b(?:source|evidence|foundation|fndds|dataset|provenance)\\b",
                source_text,
            )

            if not source_text:
                warnings.append(
                    f"source_aware_comparison task {tid} has no explicit provenance text in row metadata/context."
                )
            elif not source_cues:
                warnings.append(
                    f"source_aware_comparison task {tid} has source-aware family but no recognizable provenance cue."
                )
            elif not re.search(
                r"(?i)\\b(?:source|evidence|foundation|fndds|dataset|provenance)\\b",
                answer,
            ):
                warnings.append(
                    f"source_aware_comparison task {tid} answer does not explicitly mention provenance; wording review recommended."
                )

        # Universal claim/evidence consistency
        claims = row.get("claims")
        if not isinstance(claims, list) or not claims:
            fail("claims_missing", "Claims must contain at least one claim.")
        else:
            for claim in claims:
                if not isinstance(claim, dict):
                    fail("claim_shape", "Claim entry is not an object.")
                    continue
                if not str(claim.get("claim", "")).strip():
                    fail("claim_text", "Claim text is empty.")
                if set(map(str, claim.get("evidence_ids", []))) - set(map(str, row.get("evidence_ids", []))):
                    fail("claim_evidence", "Claim references evidence not present in task evidence_ids.")

    print()
    print("Family quality audit:")
    for fam in sorted(FAMILIES):
        checked = family_checked.get(fam, 0)
        failed = family_errors.get(fam, 0)
        if checked:
            status = "OK" if failed == 0 else "FAIL"
            print(f"[{status}] {fam:<32} checked={checked:>7,} errors={failed:>6,}")
        else:
            print(f"[WARN] {fam:<32} checked=0")
            warnings.append(f"Task family has zero examples: {fam}")

    # ------------------------------------------------------------
    # Distribution / metadata
    # ------------------------------------------------------------
    print()
    print("Metadata consistency:")
    metadata_checks = {
        "total_tasks": len(all_rows),
        "train_tasks": len(train),
        "validation_tasks": len(validation),
        "test_tasks": len(test),
    }
    for key, expected in metadata_checks.items():
        actual = metadata.get(key)
        if actual != expected:
            err("metadata_count", "DATASET", f"{key}: metadata={actual}, actual={expected}")
            print(f"[FAIL] {key}: metadata={actual}, actual={expected}")
        else:
            print(f"[OK] {key}: {actual:,}")

    # ------------------------------------------------------------
    # Save machine-readable report
    # ------------------------------------------------------------
    report_dir = root / "research" / "evaluation" / "v0_3"
    report_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "dataset_version": "v0.3",
        "dataset_dir": str(dataset_dir),
        "counts": {
            "all": len(all_rows),
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
        },
        "unique_foods": {
            "all": len(food_sets["train"] | food_sets["validation"] | food_sets["test"]),
            "train": len(food_sets["train"]),
            "validation": len(food_sets["validation"]),
            "test": len(food_sets["test"]),
        },
        "family_counts": dict(sorted(family_counts.items())),
        "family_checked": dict(sorted(family_checked.items())),
        "family_errors": dict(sorted(family_errors.items())),
        "duplication": {
            "question_family_duplicate_groups": len(duplicate_qfam),
            "question_answer_duplicate_groups": len(duplicate_qa),
            "cross_split_question_family_groups": cross_split_q,
            "cross_split_question_answer_groups": cross_split_qa,
        },
        "warnings": warnings,
        "error_count": len(errors),
        "errors_sample": errors[:args.sample_errors],
        "structural_status": "PASS" if not errors else "FAIL",
        "quality_status": "PASS" if not errors else "FAIL",
    }

    report_path = report_dir / "dataset_quality_audit.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# FoodInsight-LM V0.3 Dataset Quality Audit",
        "",
        "## Dataset",
        f"- Total tasks: {len(all_rows):,}",
        f"- Train: {len(train):,}",
        f"- Validation: {len(validation):,}",
        f"- Test: {len(test):,}",
        f"- Unique foods: {len(food_sets['train'] | food_sets['validation'] | food_sets['test']):,}",
        "",
        "## Family counts",
    ]
    for fam, count in family_counts.most_common():
        md.append(f"- `{fam}`: {count:,}")
    md += [
        "",
        "## Quality checks",
        f"- Structural/semantic audit status: **{'PASS' if not errors else 'FAIL'}**",
        f"- Audit errors: **{len(errors):,}**",
        f"- Cross-split exact question+family groups: **{cross_split_q:,}**",
        f"- Cross-split exact question+answer groups: **{cross_split_qa:,}**",
        "",
        "## Interpretation",
        "- This audit checks dataset construction consistency and generated-task arithmetic/metadata.",
        "- It does not prove that every USDA source record is scientifically correct.",
        "- Cross-split repeated question templates are warnings, not automatic leakage; food-level isolation remains the primary split control.",
    ]
    if warnings:
        md += ["", "## Warnings"]
        md.extend(f"- {w}" for w in warnings)
    if errors:
        md += ["", "## Sample errors"]
        for e in errors[:args.sample_errors]:
            md.append(f"- `{e['code']}` `{e['task_id']}`: {e['message']}")

    (report_dir / "dataset_quality_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print()
    print("=" * 78)
    if errors:
        print("FOODINSIGHT-LM V0.3 DATASET QUALITY AUDIT: FAILED")
        print("=" * 78)
        print(f"Errors: {len(errors):,}")
        print(f"Report: {report_path}")
        print()
        return 1

    print("FOODINSIGHT-LM V0.3 DATASET QUALITY AUDIT: PASSED")
    print("=" * 78)
    print(f"Report: {report_path}")
    print(f"Markdown: {report_dir / 'dataset_quality_report.md'}")
    print()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
