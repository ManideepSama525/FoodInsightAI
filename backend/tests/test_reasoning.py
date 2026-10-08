from app.reasoning.context import ReasoningContextBuilder
from app.reasoning.models import RetrievalSignal
from app.reasoning.answer_policy import AnswerPolicy

def test_hybrid_context_combines_channels():
    context=ReasoningContextBuilder().build(
        "lentils",
        vector=[RetrievalSignal(source_type="document",source_id="d1",score=.7,content="doc")],
        graph=[RetrievalSignal(source_type="graph",source_id="food:lentils",score=.8,content="graph")],
        structured=[RetrievalSignal(source_type="structured",source_id="nutrition:lentils",score=1.0,content="nutrition")],
    )
    assert len(context.evidence)==3
    assert any(x.source_type=="structured" for x in context.evidence)

def test_visual_observation_creates_uncertainty_note():
    context=ReasoningContextBuilder().build(
        "identify food",
        observations=[{"label":"possible food","confidence":.6}],
    )
    assert context.uncertainty
    assert "observations" in context.uncertainty[0]

def test_answer_policy_blocks_unsupported_categories():
    context=ReasoningContextBuilder().build("empty")
    policy=AnswerPolicy().validate(context)
    assert "invented_nutrition_value" in policy["disallowed_claim_types"]
