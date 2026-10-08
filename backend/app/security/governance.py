from datetime import datetime, timedelta, timezone
from app.security.compliance import CompliancePolicy, redact_payload

class DataGovernance:
    def __init__(self, policy: CompliancePolicy | None = None):
        self.policy = policy or CompliancePolicy()

    def sanitize_audit(self, payload: dict) -> dict:
        return redact_payload(payload, self.policy)

    def retention_cutoff(self) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=self.policy.retention_days)

    def deletion_plan(self, subject_id: str) -> dict:
        # Planning primitive: execution must be backed by durable repositories.
        return {
            "subject_id": subject_id,
            "mode": "plan",
            "retention_days": self.policy.retention_days,
            "resources": ["documents", "chunks", "query_logs", "response_logs", "feedback", "trace_events"],
            "requires_repository_execution": True,
        }

governance = DataGovernance()
