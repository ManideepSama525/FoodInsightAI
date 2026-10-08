from pydantic import BaseModel, Field

class FoodObservation(BaseModel):
    food_name: str | None = None
    visible_ingredients: list[str] = []
    preparation_characteristics: list[str] = []
    visual_observations: list[str] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty: list[str] = []
    warnings: list[str] = []

class VisionResult(BaseModel):
    observation: FoodObservation
    model: str
