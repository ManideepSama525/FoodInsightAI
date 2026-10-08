# Phase 19 — Production Workers & Event Architecture

Phase 19 strengthens the background-job boundary.

## Job guarantees

- durable SQL schema and migration for production persistence
- explicit job identity
- idempotency key support
- cancellation requests
- cancellation-aware worker boundary
- queued/running/completed/failed/cancelled lifecycle
- API cancellation endpoint
- worker isolation seam for external queues

## Production deployment boundary

The current local worker remains process-local so development stays simple. The durable database schema is ready for a shared worker implementation.

A production deployment should connect `enqueue()` to a durable queue/worker system and use the `job_records` table as the source of truth. This prevents a process restart from being treated as successful completion.

## Event architecture

The job state transitions are intentionally event-like:

```text
JOB_QUEUED
    ↓
JOB_STARTED
    ↓
JOB_PROGRESS
    ├── JOB_COMPLETED
    ├── JOB_FAILED
    └── JOB_CANCELLED
```

The system does not expose hidden model reasoning as an event.
