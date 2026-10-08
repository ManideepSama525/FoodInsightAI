from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class ApiContract:
    version: str
    status: str
    supported_versions: list[str]
    deprecated_versions: list[str]
    capabilities: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

CONTRACT = ApiContract(
    version="v1",
    status="stable",
    supported_versions=["v1"],
    deprecated_versions=[],
    capabilities=[
        "documents",
        "rag",
        "chat",
        "vision",
        "nutrition",
        "recipes",
        "safety",
        "knowledge_graph",
        "evaluation",
        "jobs",
        "observability",
        "governance",
        "recovery",
        "release_management",
    ],
)
