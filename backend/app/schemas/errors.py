from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str | None = None
