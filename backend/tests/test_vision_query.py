from app.vision.models import FoodObservation
from app.vision.query import build_retrieval_query

def test_visual_observation_becomes_retrieval_context():
    query = build_retrieval_query(
        "What is this?",
        FoodObservation(food_name="spinach", visible_ingredients=["leafy greens"])
    )
    assert "spinach" in query
    assert "leafy greens" in query
    assert "retrieve authoritative food information" in query
