from dataclasses import dataclass
from collections import defaultdict
from time import perf_counter

@dataclass
class Timer:
    started: float
    def elapsed_ms(self) -> float:
        return round((perf_counter() - self.started) * 1000, 2)

class MetricsRegistry:
    def __init__(self):
        self.counters = defaultdict(int)
        self.latencies = defaultdict(list)

    def increment(self, name: str, value: int = 1):
        self.counters[name] += value

    def observe_latency(self, name: str, milliseconds: float):
        values = self.latencies[name]
        values.append(milliseconds)
        if len(values) > 1000:
            del values[:-1000]

    def snapshot(self):
        latency = {}
        for name, values in self.latencies.items():
            if values:
                ordered = sorted(values)
                latency[name] = {
                    "count": len(values),
                    "avg_ms": round(sum(values) / len(values), 2),
                    "p50_ms": ordered[len(ordered)//2],
                    "p95_ms": ordered[min(len(ordered)-1, int(len(ordered)*0.95))],
                }
        return {"counters": dict(self.counters), "latency": latency}

metrics = MetricsRegistry()
