from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.upload import router as upload_router
from app.api.v1.routes.documents import router as documents_router
from app.api.v1.routes.ingestion import router as ingestion_router
from app.api.v1.routes.rag import router as rag_router
from app.api.v1.routes.vision import router as vision_router
from app.api.v1.routes.nutrition import router as nutrition_router
from app.api.v1.routes.recipes import router as recipes_router
from app.api.v1.routes.safety import router as safety_router
from app.api.v1.routes.traceability import router as traceability_router
from app.api.v1.routes.feedback import router as feedback_router
from app.api.v1.routes.knowledge import router as knowledge_router
from app.api.v1.routes.reasoning import router as reasoning_router
from app.api.v1.routes.research_intelligence import router as research_intelligence_router
from app.api.v1.routes.evaluation import router as evaluation_router
from app.api.v1.routes.pipeline import router as pipeline_router
from app.api.v1.routes.system import router as system_router
from app.api.v1.routes import jobs
from app.api.v1.routes.model import router as model_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(ingestion_router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(vision_router, prefix="/vision", tags=["vision"])
api_router.include_router(nutrition_router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(recipes_router, prefix="/recipes", tags=["recipes"])
api_router.include_router(safety_router, prefix="/safety", tags=["safety"])
api_router.include_router(traceability_router, prefix="/traceability", tags=["traceability"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(reasoning_router, prefix="/reasoning", tags=["reasoning"])
api_router.include_router(research_intelligence_router, prefix="/research-intelligence", tags=["research-intelligence"])
api_router.include_router(evaluation_router, prefix="/evaluation", tags=["evaluation"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(system_router, prefix="/system", tags=["system"])
api_router.include_router(model_router, prefix="/model", tags=["model"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
