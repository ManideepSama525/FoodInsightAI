import json
import re
import time
from pathlib import Path

import requests


TEST_FILE = Path(
    r"FoodInsightAI_FoodInsightLM_V0_2\research\dataset\foodinsight_lm\v0_3"
    r"\foodinsight_usda_v0_3_test.jsonl"
)

RESULTS_FILE = Path(
    r"FoodInsightAI_FoodInsightLM_V0_2\research\dataset\foodinsight_lm\v0_3"
    r"evaluation_results_v03.jsonl"
)

MODEL_URL = "http://127.0.0.1:8010/generate"
NUMERIC_TOLERANCE = 0.01


def numbers(text):
    return [
        float(x)
        for x in re.findall(r"(?<![\w.])\d+(?:\.\d+)?", text)
    ]


def contains_number(text, expected):
    return any(
        abs(v - expected) <= NUMERIC_TOLERANCE
        for v in numbers(text)
    )


def contains_text(text, value):
    return not value or str(value).lower() in text.lower()


def food_names_from_expected(row):
    expected = row["answer"]

    m = re.search(
        r"(.+?)\s+has the higher recorded .+?:.*?,\s*"
        r"compared with\s+(.+?)(?:\.|$)",
        expected,
        re.IGNORECASE,
    )

    if m:
        return m.group(1).strip(), m.group(2).strip()

    return None, None


def score_example(row, generated):
    family = row["task_family"]
    expected = row["answer"]
    generated_lower = generated.lower()

    if family == "direct_nutrient_qa":
        metadata = row.get("metadata") or {}
        nutrient = metadata.get("nutrient", "")
        unit = metadata.get("unit", "")
        expected_numbers = numbers(expected)

        value_ok = (
            any(contains_number(generated, n) for n in expected_numbers)
            if expected_numbers
            else True
        )

        return (
            value_ok
            and contains_text(generated, nutrient)
            and contains_text(generated, unit)
        )

    if family == "portion_reasoning":
        expected_numbers = numbers(expected)

        return bool(expected_numbers) and any(
            contains_number(generated, n)
            for n in expected_numbers
        )

    if family == "numerical_reasoning":
        expected_numbers = numbers(expected)

        return (
            bool(expected_numbers)
            and contains_number(generated, expected_numbers[0])
        )

    if family == "evidence_sufficiency":
        expected_yes = expected.strip().lower().startswith("yes")
        generated_yes = generated.strip().lower().startswith("yes")

        if expected_yes != generated_yes:
            return False

        expected_numbers = numbers(expected)

        if expected_numbers:
            return any(
                contains_number(generated, n)
                for n in expected_numbers
            )

        return True

    if family == "evidence_bounded_rejection":
        expected_no = expected.strip().lower().startswith("no")
        generated_no = generated.strip().lower().startswith("no")

        return expected_no == generated_no

    if family == "evidence_selection":
        food_ids = row.get("food_ids") or []

        if food_ids:
            return any(
                str(food_id).lower() in generated_lower
                for food_id in food_ids
            )

        return True

    if family == "provenance_reasoning":
        source = row.get("source", "")
        food_ids = row.get("food_ids") or []

        source_ok = (
            not source
            or source.lower() in generated_lower
        )

        food_id_ok = (
            not food_ids
            or any(
                str(food_id).lower() in generated_lower
                for food_id in food_ids
            )
        )

        return source_ok and food_id_ok

    if family == "multi_food_comparison":
        expected_a, expected_b = food_names_from_expected(row)

        if not expected_a or not expected_b:
            return (
                " ".join(generated.lower().split())
                == " ".join(expected.lower().split())
            )

        food_a_ok = expected_a.lower() in generated_lower
        food_b_ok = expected_b.lower() in generated_lower

        if not (food_a_ok and food_b_ok):
            return False

        expected_numbers = numbers(expected)

        numbers_ok = all(
            contains_number(generated, n)
            for n in expected_numbers
        )

        if not numbers_ok:
            return False

        winner_pattern = (
            re.escape(expected_a)
            + r"\s+has\s+the\s+higher"
        )

        return re.search(
            winner_pattern,
            generated,
            re.IGNORECASE,
        ) is not None

    return expected.strip().lower() in generated_lower


def load_test_rows():
    rows = []

    with TEST_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def load_completed():
    completed = {}

    if not RESULTS_FILE.exists():
        return completed

    with RESULTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            try:
                result = json.loads(line)
                completed[result["task_id"]] = result
            except Exception:
                # Ignore only an incomplete/corrupt final line.
                continue

    return completed


rows = load_test_rows()
completed = load_completed()

total = len(rows)
remaining = [row for row in rows if row["task_id"] not in completed]

print("=" * 80)
print("FoodInsightAI V0.3 RESUMABLE EVALUATION")
print("=" * 80)
print(f"Total test examples: {total}")
print(f"Already completed:   {len(completed)}")
print(f"Remaining:           {len(remaining)}")
print(f"Results file:        {RESULTS_FILE}")
print("=" * 80)

if not remaining:
    print("ALL EXAMPLES ARE ALREADY COMPLETE.")
else:
    try:
        for index, row in enumerate(remaining, 1):
            payload = {
                "question": row["question"],
                "context": row.get("context", ""),
                "max_new_tokens": 128,
            }

            start = time.perf_counter()

            response = requests.post(
                MODEL_URL,
                json=payload,
                timeout=180,
            )

            elapsed = time.perf_counter() - start
            response.raise_for_status()

            generated = response.json()["answer"]

            passed = score_example(row, generated)

            result = {
                "task_id": row["task_id"],
                "task_family": row["task_family"],
                "passed": passed,
                "expected": row["answer"],
                "generated": generated,
                "latency": round(elapsed, 3),
            }

            # IMPORTANT:
            # Write immediately after every completed example.
            with RESULTS_FILE.open("a", encoding="utf-8") as out:
                out.write(json.dumps(result, ensure_ascii=False) + "\n")
                out.flush()

            completed[row["task_id"]] = result

            done = len(completed)

            print(
                f"[{done:04d}/{total}] "
                f"{row['task_family']:<28} "
                f"{'PASS' if passed else 'FAIL':<4} "
                f"{elapsed:.2f}s"
            )

            if not passed:
                print(f"  Expected:  {row['answer']}")
                print(f"  Generated: {generated}")

    except KeyboardInterrupt:
        print("\n")
        print("=" * 80)
        print("EVALUATION STOPPED SAFELY")
        print("=" * 80)
        print(f"Saved completed examples: {len(completed)}/{total}")
        print("Run the same command again to continue.")
        raise SystemExit(0)

    except Exception as exc:
        print("\n")
        print("=" * 80)
        print("EVALUATION STOPPED BECAUSE OF AN ERROR")
        print("=" * 80)
        print(repr(exc))
        print(f"Saved completed examples: {len(completed)}/{total}")
        print("Run the same command again to continue.")
        raise


# ------------------------------------------------------------------
# Statistics over everything completed so far
# ------------------------------------------------------------------

all_results = list(completed.values())

print("\n" + "=" * 80)
print("CURRENT RESULTS")
print("=" * 80)

if not all_results:
    print("No completed examples.")
    raise SystemExit(0)

total_pass = sum(r["passed"] for r in all_results)
count = len(all_results)

print(f"Completed:     {count}/{total}")
print(f"Remaining:     {total - count}")
print(f"Task accuracy: {total_pass}/{count} = {total_pass / count:.2%}")
print(
    f"Average latency: "
    f"{sum(r['latency'] for r in all_results) / count:.3f} s"
)

print("\nBY TASK FAMILY")
print("-" * 80)

families = {}

for result in all_results:
    families.setdefault(result["task_family"], []).append(result)

for family, family_results in sorted(families.items()):
    passed = sum(r["passed"] for r in family_results)
    family_count = len(family_results)

    print(
        f"{family:<28} "
        f"{passed}/{family_count} = "
        f"{passed / family_count:.2%}"
    )

if count == total:
    print("\n" + "=" * 80)
    print("FINAL EVALUATION COMPLETE")
    print("=" * 80)
