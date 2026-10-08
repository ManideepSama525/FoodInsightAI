from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass
class FoodInsightEvalSummary:
    total: int
    nonempty: int
    numeric_claim_cases: int
    numeric_mismatch_cases: int
    unsupported_numeric_rate: float


_NUM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:g|mg|kg|kcal|%|mcg|µg)\b", re.I)


def evaluate_records(records: Iterable[dict]) -> FoodInsightEvalSummary:
    rows = list(records)
    numeric_cases = 0
    numeric_mismatches = 0
    nonempty = 0

    for row in rows:
        pred = str(row.get("prediction", "")).strip()
        evidence = str(row.get("expected", "")).strip()
        if pred:
            nonempty += 1

        pred_nums = {x.group(0).lower().replace(" ", "") for x in _NUM.finditer(pred)}
        exp_nums = {x.group(0).lower().replace(" ", "") for x in _NUM.finditer(evidence)}
        if pred_nums:
            numeric_cases += 1
            if exp_nums and not (pred_nums & exp_nums):
                numeric_mismatches += 1

    rate = numeric_mismatches / numeric_cases if numeric_cases else 0.0
    return FoodInsightEvalSummary(
        total=len(rows),
        nonempty=nonempty,
        numeric_claim_cases=numeric_cases,
        numeric_mismatch_cases=numeric_mismatches,
        unsupported_numeric_rate=rate,
    )
