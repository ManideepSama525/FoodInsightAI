# Phase 18 — Real-Time Intelligence

Phase 18 introduces a development-grade background job layer and live frontend status tracking.

## Job lifecycle

```text
queued → running → completed
                 ↘ failed
```

Jobs expose:
- ID
- kind
- subject
- progress
- status
- message
- result/error
- timestamps

## Current asynchronous flow

Document → enqueue ingestion → background worker → progress updates → persisted indexed state.

The store is intentionally process-local for development. Production deployment should move job state and workers to a shared queue/store such as Redis plus a worker system, with durable job records.

The frontend polls the job endpoint and displays progress without exposing internal reasoning.
