from pydantic import BaseModel

class PipelineRequest(BaseModel):
    query: str
    image_id: str | None = None
    mode: str = "assistant"

class PipelineStage(BaseModel):
    name: str
    status: str
    details: dict = {}

class PipelineResult(BaseModel):
    query: str
    answer: str
    grounded: bool
    stages: list[PipelineStage] = []
    uncertainty: list[str] = []
    provenance: list[dict] = []
