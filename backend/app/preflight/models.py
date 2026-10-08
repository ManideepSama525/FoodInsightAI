from dataclasses import dataclass, asdict
from typing import Any
@dataclass(frozen=True)
class PreflightCheck:
    name: str
    passed: bool
    severity: str
    detail: str
    def as_dict(self) -> dict[str, Any]: return asdict(self)
@dataclass(frozen=True)
class PreflightReport:
    ready: bool
    generated_at: str
    checks: list[PreflightCheck]
    blockers: list[str]
    warnings: list[str]
    def as_dict(self) -> dict[str, Any]:
        return {"ready":self.ready,"generated_at":self.generated_at,
                "checks":[c.as_dict() for c in self.checks],
                "blockers":self.blockers,"warnings":self.warnings}
