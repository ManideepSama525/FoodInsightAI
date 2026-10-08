# Phase 33 — Production Preflight & Launch Controls

Adds explicit production startup/deployment invariants for database configuration,
API security, secrets, and CORS.

Endpoint: `GET /api/v1/system/preflight`

Production is blocked when required security/configuration invariants are missing.
Development remains permissive for local workflows. This is a launch gate, not a guarantee
of application correctness or infrastructure availability.
