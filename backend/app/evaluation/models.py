from pydantic import BaseModel, Field

class EvalCase(BaseModel):
    case_id: str
    category: str
    query: str
    expected: dict
    inputs: dict = {}

class EvalMetric(BaseModel):
    name: str
    value: float = Field(ge=0, le=1)
    details: dict = {}

class EvalResult(BaseModel):
    case_id: str
    category: str
    passed: bool
    metrics: list[EvalMetric] = []
    notes: list[str] = []

class EvalReport(BaseModel):
    total_cases: int
    passed_cases: int
    pass_rate: float = Field(ge=0, le=1)
    metrics: list[EvalMetric] = []
    results: list[EvalResult] = []
