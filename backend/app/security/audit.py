from datetime import datetime, timezone
from structlog import get_logger

logger=get_logger(__name__)

def audit_event(event: str, request_id: str | None = None, **fields):
    # Never log secrets, API keys, authorization headers, or request bodies.
    logger.info(
        "security_audit",
        event=event,
        request_id=request_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **fields,
    )
