from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class BackupStatus(str, Enum):
    PLANNED = "planned"
    VERIFIED = "verified"
    FAILED = "failed"

@dataclass(frozen=True)
class RecoveryObjectives:
    rpo_minutes: int = 60
    rto_minutes: int = 120

@dataclass
class BackupManifest:
    backup_id: str
    created_at: str
    source: str
    status: BackupStatus
    object_count: int = 0
    checksum: str | None = None
    size_bytes: int = 0

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

@dataclass(frozen=True)
class RestoreVerification:
    backup_id: str
    verified_at: str
    checks: dict[str, bool]
    passed: bool
    notes: str = ""

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
