from fastapi import APIRouter
from app.evaluation.runner import EvaluationRunner
from app.evaluation.sample_cases import demo_cases

router=APIRouter()

@router.post("/run")
async def run_evaluation():
    report=EvaluationRunner().run(demo_cases())
    return report
