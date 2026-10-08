from pydantic import BaseModel, Field

class RecipeIngredient(BaseModel):
    name: str
    quantity: str
    notes: str | None = None

class RecipeRequest(BaseModel):
    dish_name: str
    servings: int = Field(default=2, ge=1, le=20)
    dietary_constraints: list[str] = []
    allergies: list[str] = []
    excluded_ingredients: list[str] = []
    available_ingredients: list[str] = []
    goals: list[str] = []

class Recipe(BaseModel):
    name: str
    servings: int
    ingredients: list[RecipeIngredient]
    steps: list[str]
    substitutions: list[str] = []
    constraint_notes: list[str] = []
    nutrition_basis: list[str] = []
    safety_notes: list[str] = []
