from dataclasses import dataclass

@dataclass
class ComponentStatus:
    name: str
    status: str
    detail: str

class DependencyHealth:
    def check(self) -> list[ComponentStatus]:
        # Connectivity checks are intentionally separated from application
        # logic; deployment can replace these with live DB/vector/LLM probes.
        return [
            ComponentStatus("postgresql", "configured", "Async SQLAlchemy session available"),
            ComponentStatus("qdrant", "configured", "Vector-store adapter available"),
            ComponentStatus("llm", "configured", "Provider abstraction available"),
            ComponentStatus("vision", "configured", "Vision provider abstraction available"),
        ]
