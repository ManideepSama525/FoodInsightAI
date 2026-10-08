from app.evaluation.models import EvalCase

def demo_cases() -> list[EvalCase]:
    return [
        EvalCase(
            case_id="retrieval-001",
            category="retrieval",
            query="lentils",
            expected={"relevant_ids":["food:lentils"],"k":3,"minimum_metric":0.8},
            inputs={"actual":{"retrieved_ids":["food:lentils","food:rice","food:spinach"]}},
        ),
        EvalCase(
            case_id="citation-001",
            category="grounding",
            query="What supports this answer?",
            expected={"required_citations":["doc-1"],"minimum_metric":0.8},
            inputs={"actual":{"cited_ids":["doc-1"]}},
        ),
        EvalCase(
            case_id="nutrition-001",
            category="nutrition",
            query="Calculate nutrition",
            expected={"minimum_metric":0.8},
            inputs={"actual":{"violations":[]}},
        ),
        EvalCase(
            case_id="resolution-001",
            category="entity_resolution",
            query="dal",
            expected={"expected_answer":"cooked lentils","minimum_metric":0.8},
            inputs={"actual":{"answer":"cooked lentils"}},
        ),
        EvalCase(
            case_id="multimodal-001",
            category="multimodal",
            query="image observation",
            expected={"expected_answer":"observation uncertainty","minimum_metric":0.8},
            inputs={"actual":{"answer":"observation uncertainty"}},
        ),
    ]
