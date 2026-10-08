# Phase 12 — Production Service Wiring and End-to-End Orchestration

Phase 12 establishes the application-level pipeline boundary:

```text
UNDERSTAND
    ↓
RETRIEVE
    ↓
REASON
    ↓
VALIDATE
    ↓
RESPOND
```

## API

- `POST /api/v1/pipeline/run`
- `GET /api/v1/pipeline/health`

The pipeline exposes operational stage status, grounding state, uncertainty, and provenance.
It deliberately does not expose hidden chain-of-thought.

## Persistence integration

Phase 11 introduced durable PostgreSQL models and repositories. Phase 12 keeps the repositories
as independently injectable components so services can migrate from their development stores
without changing API contracts.

## Production wiring

A deployment should provide:
- PostgreSQL connectivity and completed Alembic migrations
- Qdrant/vector-store configuration
- an approved LLM provider
- an approved vision provider
- authoritative nutrition/safety sources
- observability and request correlation

The current pipeline remains conservative when no evidence is available.
