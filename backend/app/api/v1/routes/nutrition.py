from fastapi import APIRouter, HTTPException, Query
from app.nutrition.service import NutritionService

router = APIRouter()
service = NutritionService()

@router.get("/search")
async def search_foods(q: str = Query(min_length=1, max_length=200)):
    return {"results": service.search(q)}

@router.get("/{food_id}")
async def nutrition(food_id: str, serving_g: float = Query(default=100, gt=0)):
    try:
        return service.estimate(food_id, serving_g)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
