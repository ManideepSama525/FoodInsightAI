from contextlib import contextmanager
from time import perf_counter
from uuid import uuid4
import structlog

@contextmanager
def span(name: str, correlation_id: str | None = None):
    cid = correlation_id or str(uuid4())
    started = perf_counter()
    log = structlog.get_logger().bind(span=name, correlation_id=cid)
    log.info("span_start")
    try:
        yield cid
        log.info("span_end", duration_ms=round((perf_counter()-started)*1000, 2))
    except Exception:
        log.exception("span_error", duration_ms=round((perf_counter()-started)*1000, 2))
        raise
