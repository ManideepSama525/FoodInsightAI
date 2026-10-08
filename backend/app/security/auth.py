from fastapi import Header, HTTPException
from app.security.config import security_settings

async def require_api_key(x_api_key: str | None = Header(default=None)):
    if not security_settings.require_api_key:
        return None
    if not security_settings.api_key:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if x_api_key != security_settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
