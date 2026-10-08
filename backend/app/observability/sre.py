from dataclasses import dataclass
import os

@dataclass(frozen=True)
class SREThresholds:
    p95_latency_ms: int = int(os.getenv("FOODINSIGHT_P95_LATENCY_MS", "3000"))
    error_rate_percent: float = float(os.getenv("FOODINSIGHT_ERROR_RATE_PERCENT", "5"))
    worker_stale_seconds: int = int(os.getenv("FOODINSIGHT_WORKER_STALE_SECONDS", "60"))

def evaluate(snapshot: dict, thresholds: SREThresholds | None = None) -> dict:
    t = thresholds or SREThresholds()
    latency = snapshot.get("latency", {})
    counters = snapshot.get("counters", {})
    violations = []

    for name, value in latency.items():
        if value.get("p95_ms", 0) > t.p95_latency_ms:
            violations.append({
                "type": "latency",
                "metric": name,
                "p95_ms": value["p95_ms"],
                "threshold_ms": t.p95_latency_ms,
            })

    total = sum(v for k,v in counters.items() if k.endswith("_total") and not k.endswith("errors_total"))
    errors = sum(v for k,v in counters.items() if "error" in k)
    rate = (errors / total * 100) if total else 0
    if rate > t.error_rate_percent:
        violations.append({
            "type": "error_rate",
            "rate_percent": round(rate, 2),
            "threshold_percent": t.error_rate_percent,
        })

    return {"healthy": not violations, "violations": violations}
