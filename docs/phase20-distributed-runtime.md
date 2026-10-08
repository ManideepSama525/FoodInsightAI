# Phase 20 — Distributed Production Runtime

Phase 20 establishes the deployment boundary for distributed job execution.

```text
FastAPI → Redis queue/events → worker replicas → PostgreSQL state
```

Added:
- optional async Redis coordination
- Redis job/event primitives
- configurable worker concurrency
- queue and dead-letter queue names
- isolated worker entrypoint
- worker Dockerfile
- production Compose overlay
- persistent Redis volume
- two-worker deployment intent

The process-local job store remains available for development. Production should use the distributed runtime and a durable consumer/retry policy.
