from pydantic import BaseModel, Field

class NutrientProfile(BaseModel):
    calories_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbohydrates_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    fiber_g: float = Field(default=0, ge=0)
    sodium_mg: float = Field(default=0, ge=0)

class FoodRecord(BaseModel):
    food_id: str
    name: str
    serving_g: float = Field(gt=0)
    nutrients: NutrientProfile
    source: str
    synthetic: bool = False

class NutritionEstimate(BaseModel):
    food_id: str
    food_name: str
    requested_serving_g: float
    nutrients: NutrientProfile
    source: str
    synthetic: bool = False
