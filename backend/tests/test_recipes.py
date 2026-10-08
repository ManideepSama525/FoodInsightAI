from app.recipes.models import RecipeRequest
from app.recipes.service import RecipeService

def test_recipe_respects_allergy():
    recipe = RecipeService().generate_demo(
        RecipeRequest(dish_name="Lentil Rice Bowl", allergies=["peanut"])
    )
    assert all("peanut" not in i.name.lower() for i in recipe.ingredients)
    assert recipe.substitutions

def test_recipe_has_structured_constraints():
    recipe = RecipeService().generate_demo(
        RecipeRequest(
            dish_name="Lentil Rice Bowl",
            servings=4,
            dietary_constraints=["vegetarian"],
        )
    )
    assert recipe.servings == 4
    assert recipe.constraint_notes
    assert recipe.nutrition_basis
