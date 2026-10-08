from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    severity: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    checks: list[ReadinessCheck]
    blockers: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "checks": [c.as_dict() for c in self.checks],
            "blockers": self.blockers,
        }
