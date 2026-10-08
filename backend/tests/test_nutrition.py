from app.nutrition.service import NutritionService

def test_nutrition_scales_by_serving():
    estimate = NutritionService().estimate("demo-rice-cooked", 200)
    assert estimate.nutrients.calories_kcal == 260
    assert estimate.nutrients.carbohydrates_g == 56.4
    assert estimate.synthetic is True

def test_unknown_food_fails():
    try:
        NutritionService().estimate("missing", 100)
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("Expected missing food to fail")
