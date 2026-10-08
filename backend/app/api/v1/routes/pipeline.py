from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.orchestration.models import PipelineRequest, PipelineResult
from app.orchestration.pipeline import ProductionPipeline
from app.orchestration.health import DependencyHealth
from app.repositories.documents import DocumentRepository
from app.vision.service import VisionService

router = APIRouter()
pipeline = ProductionPipeline()
health = DependencyHealth()


@router.post("/run", response_model=PipelineResult)
async def run_pipeline(
    request: PipelineRequest,
    db: AsyncSession = Depends(get_db),
):
    vision_result = None

    if request.image_id:
        image_document = await DocumentRepository(db).get(
            request.image_id
        )

        if not image_document:
            raise HTTPException(
                status_code=404,
                detail="Image document not found.",
            )

        if image_document.document_type != "image":
            raise HTTPException(
                status_code=400,
                detail="image_id must refer to an image.",
            )

        try:
            vision_result = await VisionService().analyze(
                image_document.storage_path
            )
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Image analysis failed: {exc}",
            ) from exc

    return await pipeline.run(
        request,
        vision_result=vision_result,
    )


@router.get("/health")
async def pipeline_health():
    return {
        "components": [x.__dict__ for x in health.check()]
    }
