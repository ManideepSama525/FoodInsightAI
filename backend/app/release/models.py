from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True)
class ReleaseManifest:
    version: str
    generated_at: str
    git_ref: str
    schema_revision: str
    features: dict[str, bool]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class CompatibilityResult:
    compatible: bool
    application_version: str
    required_schema_revision: str
    current_schema_revision: str
    reason: str

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
