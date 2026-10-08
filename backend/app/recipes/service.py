from app.recipes.models import Recipe, RecipeRequest, RecipeIngredient

class RecipeService:
    def generate_demo(self, request: RecipeRequest) -> Recipe:
        # Deterministic domain scaffold. A production LLM can generate the
        # candidate recipe, but this service remains the constraint validator.
        excluded = {x.lower() for x in request.excluded_ingredients + request.allergies}
        if any("peanut" in x for x in excluded):
            base = [
                RecipeIngredient(name="cooked lentils", quantity="2 cups"),
                RecipeIngredient(name="cooked rice", quantity="2 cups"),
                RecipeIngredient(name="spinach", quantity="2 cups"),
            ]
            substitutions = ["Use a seed or legume-based topping instead of peanut-based toppings."]
        else:
            base = [
                RecipeIngredient(name="cooked lentils", quantity="2 cups"),
                RecipeIngredient(name="cooked rice", quantity="2 cups"),
                RecipeIngredient(name="spinach", quantity="2 cups"),
            ]
            substitutions = []

        violations = [
            ingredient.name for ingredient in base
            if ingredient.name.lower() in excluded
        ]
        if violations:
            raise ValueError(f"Recipe constraint violation: {violations}")

        notes = []
        if request.dietary_constraints:
            notes.append(
                "Requested dietary constraints: " +
                ", ".join(request.dietary_constraints)
            )
        if request.allergies:
            notes.append(
                "Allergy exclusions applied: " + ", ".join(request.allergies)
            )
        if request.available_ingredients:
            notes.append(
                "Available ingredients supplied by user: " +
                ", ".join(request.available_ingredients)
            )

        return Recipe(
            name=request.dish_name,
            servings=request.servings,
            ingredients=base,
            steps=[
                "Combine the cooked lentils and rice.",
                "Add spinach and mix according to the desired texture.",
                "Season using ingredients compatible with the stated constraints.",
            ],
            substitutions=substitutions,
            constraint_notes=notes,
            nutrition_basis=[
                "Nutrition must be calculated from matched food records and stated serving sizes.",
                "This demo recipe does not claim a complete nutritional profile."
            ],
            safety_notes=[
                "Verify ingredient labels and cross-contact risks for declared allergies."
            ],
        )
