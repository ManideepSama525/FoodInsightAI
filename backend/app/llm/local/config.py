
from pydantic import BaseModel, Field


class LocalModelConfig(BaseModel):
    model_id: str = Field(
        default="REPLACE_WITH_OPEN_WEIGHT_MODEL",
        description="Hugging Face model ID or local model directory.",
    )
    revision: str | None = None
    device: str = "auto"
    max_new_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.9
    trust_remote_code: bool = False
    load_in_4bit: bool = False
    load_in_8bit: bool = False
