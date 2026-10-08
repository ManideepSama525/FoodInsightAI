from app.evaluation.metrics import (
    citation_coverage,
    constraint_satisfaction,
    recall_at_k,
)
from app.evaluation.runner import EvaluationRunner
from app.evaluation.sample_cases import demo_cases

def test_metrics():
    assert recall_at_k(["a"], ["b","a"], 2) == 1.0
    assert citation_coverage(["x"], ["x"]) == 1.0
    assert constraint_satisfaction([]) == 1.0

def test_demo_evaluation():
    report=EvaluationRunner().run(demo_cases())
    assert report.total_cases == 5
    assert report.pass_rate == 1.0
