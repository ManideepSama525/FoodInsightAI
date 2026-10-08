from fastapi import Request
from fastapi.responses import JSONResponse
from app.security.config import security_settings
from app.security.rate_limit import InMemoryRateLimiter
from app.security.audit import audit_event

limiter=InMemoryRateLimiter(security_settings.rate_limit_per_minute)

async def security_middleware(request: Request, call_next):
    content_length=request.headers.get("content-length")
    if content_length and int(content_length) > security_settings.max_request_body_bytes:
        return JSONResponse(status_code=413, content={"detail":"Request body too large"})

    client=request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        audit_event("rate_limit_exceeded", client=client, path=request.url.path)
        return JSONResponse(status_code=429, content={"detail":"Rate limit exceeded"})

    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["Cache-Control"]="no-store"
    return response
