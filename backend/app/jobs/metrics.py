from collections import Counter

class JobMetrics:
    def __init__(self):
        self.counters = Counter()

    def observe(self, status: str):
        self.counters[f"jobs_{status}_total"] += 1

    def snapshot(self) -> dict[str, int]:
        return dict(self.counters)

metrics = JobMetrics()
