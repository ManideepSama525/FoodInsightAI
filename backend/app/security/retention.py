from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

@dataclass(frozen=True)
class RetentionItem:
    resource: str
    created_at: datetime
    retention_days: int

    @property
    def eligible(self) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        return self.created_at < cutoff

class RetentionPlanner:
    def plan(self, items: list[RetentionItem]) -> list[dict]:
        return [
            {
                "resource": item.resource,
                "created_at": item.created_at.isoformat(),
                "action": "delete" if item.eligible else "retain",
            }
            for item in items
        ]

retention_planner = RetentionPlanner()
