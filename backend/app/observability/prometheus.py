from app.observability.metrics import metrics

def exposition() -> str:
    snapshot = metrics.snapshot()
    lines = [
        "# HELP foodinsight_http_requests_total Total HTTP requests.",
        "# TYPE foodinsight_http_requests_total counter",
        f"foodinsight_http_requests_total {snapshot['counters'].get('http_requests_total', 0)}",
    ]
    for name, value in sorted(snapshot["counters"].items()):
        if name == "http_requests_total":
            continue
        metric = name if name.startswith("foodinsight_") else f"foodinsight_{name}"
        lines.extend([
            f"# TYPE {metric} counter",
            f"{metric} {value}",
        ])
    for name, data in snapshot["latency"].items():
        base = f"foodinsight_{name}"
        lines.extend([
            f"# TYPE {base}_p95_ms gauge",
            f"{base}_p95_ms {data['p95_ms']}",
            f"# TYPE {base}_avg_ms gauge",
            f"{base}_avg_ms {data['avg_ms']}",
        ])
    return "\n".join(lines) + "\n"
