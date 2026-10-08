from __future__ import annotations

from pydantic import BaseModel, Field


class NumericalCalculation(BaseModel):
    nutrient: str
    value_per_100g: float = Field(ge=0)
    portion_grams: float = Field(gt=0)
    calculated_value: float = Field(ge=0)
    unit: str
    formula: str
    evidence_id: str
    food_id: str
    food_name: str
    source: str
