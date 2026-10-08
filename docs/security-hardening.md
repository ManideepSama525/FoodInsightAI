# Phase 13 — Security, Observability and Production Hardening

## Security controls

Added:
- environment-driven API-key authentication hook
- configurable request rate limiting
- request-body size guard
- security response headers
- security audit logging
- live/readiness probes

## Authentication

Authentication is disabled by default for local development.

Production can set:

```text
FOODINSIGHT_REQUIRE_API_KEY=true
FOODINSIGHT_API_KEY=<secret>
```

Secrets must be injected through a deployment secret manager or protected environment,
not committed to source control.

## Rate limiting

The current limiter is process-local and suitable only as a development/low-scale guard.
Production deployments with multiple replicas should use a shared limiter such as Redis.

## Audit logging

Audit events deliberately exclude:
- API keys
- authorization headers
- request bodies
- other secret material

## Probes

- `GET /api/v1/system/live`
- `GET /api/v1/system/ready`
- `GET /api/v1/system/security`

The readiness service currently reports configured dependency boundaries rather than pretending
that every external dependency has been live-tested.

## Production checklist

Before production:
1. Enable authentication.
2. Put secrets in a secret manager.
3. Replace process-local rate limiting with shared state.
4. Configure TLS at the edge.
5. Restrict CORS to known origins.
6. Enable centralized structured logs.
7. Add metrics and distributed tracing.
8. Run database migrations before application rollout.
9. Set conservative upload/request limits.
10. Review audit retention and privacy requirements.
