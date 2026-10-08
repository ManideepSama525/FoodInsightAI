from pydantic import BaseModel, Field

class LLMSourceRef(BaseModel):
    source_index: int = Field(ge=1)

class LLMResponse(BaseModel):
    answer: str
    source_refs: list[LLMSourceRef] = []
    uncertainty: str | None = None
    unsupported_claims: list[str] = []
