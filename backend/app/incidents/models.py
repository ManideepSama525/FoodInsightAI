from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class IncidentSignal:
    source: str
    status: str
    detail: str
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class IncidentReport:
    generated_at: str
    severity: str
    status: str
    signals: list[IncidentSignal]
    recommended_actions: list[str]
    def as_dict(self) -> dict[str, Any]:
        return {"generated_at": self.generated_at, "severity": self.severity,
                "status": self.status, "signals": [s.as_dict() for s in self.signals],
                "recommended_actions": self.recommended_actions}
