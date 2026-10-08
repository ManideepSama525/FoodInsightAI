from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    document_type: str
    mime_type: str | None
    status: str
    source: str | None
    created_at: datetime

class DocumentList(BaseModel):
    items: list[DocumentOut]
    total: int
