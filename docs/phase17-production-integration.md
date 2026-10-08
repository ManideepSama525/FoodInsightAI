# Phase 17 — Production Integration

Phase 17 connects the workbench to the persistent document lifecycle and operational API surfaces.

## Integrated flows

- API readiness check
- document listing
- upload with XMLHttpRequest progress
- source selection
- ingestion trigger
- image analysis trigger
- grounded chat
- citation cards
- retry-aware API client
- user-visible error states
- persisted source identity

## Architecture

```text
Frontend
  │
  ├── readiness
  ├── documents
  ├── upload + progress
  ├── ingestion
  ├── vision
  └── chat + citations
        │
        ▼
FastAPI API
        │
        ▼
Persistence / RAG / Vision / LLM
```

The client retries transient request failures, but backend state remains authoritative.
