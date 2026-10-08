from app.nutrition.catalog import FoodCatalog
from app.nutrition.models import NutritionEstimate, NutrientProfile

class NutritionService:
    def __init__(self, catalog: FoodCatalog | None = None):
        self.catalog = catalog or FoodCatalog()

    def estimate(self, food_id: str, serving_g: float) -> NutritionEstimate:
        record = self.catalog.get(food_id)
        if not record:
            raise ValueError(f"Food record not found: {food_id}")
        if serving_g <= 0:
            raise ValueError("Serving size must be greater than zero.")

        scale = serving_g / record.serving_g
        n = record.nutrients
        nutrients = NutrientProfile(
            calories_kcal=n.calories_kcal * scale,
            protein_g=n.protein_g * scale,
            carbohydrates_g=n.carbohydrates_g * scale,
            fat_g=n.fat_g * scale,
            fiber_g=n.fiber_g * scale,
            sodium_mg=n.sodium_mg * scale,
        )
        return NutritionEstimate(
            food_id=record.food_id,
            food_name=record.name,
            requested_serving_g=serving_g,
            nutrients=nutrients,
            source=record.source,
            synthetic=record.synthetic,
        )

    def search(self, query: str) -> list[dict]:
        return [r.model_dump() for r in self.catalog.search(query)]
