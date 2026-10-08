from pydantic import BaseModel, Field
import os

class SecuritySettings(BaseModel):
    api_key: str | None = os.getenv("FOODINSIGHT_API_KEY")
    require_api_key: bool = os.getenv("FOODINSIGHT_REQUIRE_API_KEY", "false").lower() == "true"
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    max_request_body_bytes: int = Field(default=10_000_000, ge=1024)

security_settings = SecuritySettings()
