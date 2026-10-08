# Phase 24 — Security, Privacy & Data Governance

Phase 24 establishes a privacy/compliance boundary around operational telemetry and data lifecycle workflows.

## Added

- configurable retention policy object
- recursive PII/secret redaction for audit payloads
- email and phone redaction
- API-key/secret redaction
- retention-cutoff calculation
- data-subject deletion planning primitive
- compliance policy endpoint
- frontend privacy/retention status panel

## Important boundary

The deletion endpoint intentionally produces a **plan**, not an irreversible deletion. Durable execution must be connected to repository-level deletion transactions and authorization before production use.

## Endpoint

- `GET /api/v1/system/compliance`
- `POST /api/v1/system/data-subjects/{subject_id}/deletion-plan`
