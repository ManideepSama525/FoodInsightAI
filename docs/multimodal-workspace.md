# Phase 15 — Multimodal Document & Image Workspace

The frontend now provides a unified source-to-answer workflow.

## Workflow

```text
Upload document/image
        ↓
Source record
        ↓
Image observation (when applicable)
        ↓
Grounded conversation
        ↓
Sources / citations
```

The workspace keeps source identity visible and distinguishes visual observations from authoritative evidence.

## Current UI

- document/image file selection
- upload action
- image-analysis action
- source metadata
- grounded chat
- citation/provenance surface
- responsive workspace layout

The backend remains authoritative for validation, storage, retrieval, reasoning, and safety constraints.
