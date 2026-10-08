from datetime import datetime, timezone

class Heartbeat:
    def __init__(self):
        self.last_seen = datetime.now(timezone.utc)

    def beat(self):
        self.last_seen = datetime.now(timezone.utc)

    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.last_seen).total_seconds()
