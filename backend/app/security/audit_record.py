from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

@dataclass(frozen=True)
class AuditRecord:
    event_id: str
    timestamp: datetime
    actor: str
    action: str
    resource: str
    decision: str
    reason: str

def make_audit_record(actor: str, action: str, resource: str, decision: str, reason: str) -> AuditRecord:
    return AuditRecord(
        event_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc),
        actor=actor,
        action=action,
        resource=resource,
        decision=decision,
        reason=reason,
    )
