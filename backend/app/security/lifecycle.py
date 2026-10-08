from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class LifecycleEvent:
    resource: str
    action: str
    timestamp: datetime
    retention_applied: bool = True

def mark_for_retention(resource: str) -> LifecycleEvent:
    return LifecycleEvent(resource, "retention_registered", datetime.now(timezone.utc))

def mark_for_deletion(resource: str) -> LifecycleEvent:
    return LifecycleEvent(resource, "deletion_requested", datetime.now(timezone.utc))
