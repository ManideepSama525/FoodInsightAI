
from app.evaluation.foodinsight_v03 import evaluate_records


def test_eval_summary():
    result = evaluate_records([
        {"prediction": "Protein: 8 g", "expected": "Protein: 8 g"},
        {"prediction": "Protein: 20 g", "expected": "Protein: 8 g"},
        {"prediction": "No numeric claim", "expected": "Reference"},
    ])
    assert result.total == 3
    assert result.nonempty == 3
    assert result.numeric_claim_cases == 2
    assert result.numeric_mismatch_cases == 1
    assert result.unsupported_numeric_rate == 0.5
