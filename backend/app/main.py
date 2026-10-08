from fastapi import FastAPI
from app.api_contract.headers import add_contract_headers, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.request_id import RequestIdMiddleware
from app.security.middleware import security_middleware
from app.jobs.service import shutdown as shutdown_jobs
from app.observability.middleware import observability_middleware

configure_logging(settings.log_level)

app = FastAPI(
    title="FoodInsightAI API",
    version="0.2.0",
    description="Multimodal, retrieval-grounded AI system for food intelligence.",
)

app.middleware("http")(security_middleware)
app.middleware("http")(observability_middleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(add_contract_headers)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "foodinsightai-backend"}

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    import structlog
    import traceback

    structlog.get_logger().exception(
        "unhandled_exception",
        path=str(request.url),
        error_type=type(exc).__name__,
        error=str(exc),
        traceback=traceback.format_exc(),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "detail": f"{type(exc).__name__}: {exc}",
        },
    )

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_jobs()
