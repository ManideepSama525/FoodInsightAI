from fastapi import APIRouter, HTTPException
from app.recipes.models import RecipeRequest
from app.recipes.service import RecipeService

router = APIRouter()
service = RecipeService()

@router.post("/generate")
async def generate_recipe(request: RecipeRequest):
    try:
        return service.generate_demo(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
