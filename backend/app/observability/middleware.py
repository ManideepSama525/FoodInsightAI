from time import perf_counter
import structlog
from app.observability.metrics import metrics

async def observability_middleware(request, call_next):
    started = perf_counter()
    request_id = request.headers.get("x-request-id", "generated")
    log = structlog.get_logger().bind(request_id=request_id, path=str(request.url.path))
    metrics.increment("http_requests_total")
    try:
        response = await call_next(request)
        metrics.increment(f"http_status_{response.status_code}_total")
        if response.status_code >= 500:
            metrics.increment("http_errors_total")
        return response
    finally:
        metrics.observe_latency("http_request", (perf_counter()-started)*1000)
        log.info("http_request_complete")
