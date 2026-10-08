from app.nutrition.models import FoodRecord, NutrientProfile

# Clearly labeled demo data. Replace/extend with a curated authoritative food
# composition source in production; these values are not presented as scientific
# ground truth.
SYNTHETIC_FOODS = [
    FoodRecord(
        food_id="demo-rice-cooked",
        name="Cooked white rice",
        serving_g=100,
        nutrients=NutrientProfile(
            calories_kcal=130, protein_g=2.7, carbohydrates_g=28.2,
            fat_g=0.3, fiber_g=0.4, sodium_mg=1
        ),
        source="FoodInsightAI synthetic demo catalog",
        synthetic=True,
    ),
    FoodRecord(
        food_id="demo-lentils-cooked",
        name="Cooked lentils",
        serving_g=100,
        nutrients=NutrientProfile(
            calories_kcal=116, protein_g=9.0, carbohydrates_g=20.1,
            fat_g=0.4, fiber_g=7.9, sodium_mg=2
        ),
        source="FoodInsightAI synthetic demo catalog",
        synthetic=True,
    ),
    FoodRecord(
        food_id="demo-spinach-raw",
        name="Raw spinach",
        serving_g=100,
        nutrients=NutrientProfile(
            calories_kcal=23, protein_g=2.9, carbohydrates_g=3.6,
            fat_g=0.4, fiber_g=2.2, sodium_mg=79
        ),
        source="FoodInsightAI synthetic demo catalog",
        synthetic=True,
    ),
]

class FoodCatalog:
    def __init__(self, records: list[FoodRecord] | None = None):
        self.records = records or SYNTHETIC_FOODS

    def search(self, query: str) -> list[FoodRecord]:
        q = query.lower().strip()
        return [
            record for record in self.records
            if q in record.name.lower() or q in record.food_id.lower()
        ]

    def get(self, food_id: str) -> FoodRecord | None:
        return next((r for r in self.records if r.food_id == food_id), None)
