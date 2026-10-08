# Phase 26 — Governed Operations

Phase 26 connects policy decisions to operational actions rather than leaving them as passive diagnostics.

## Added

- centralized `AccessService`
- authorization + audit record in one decision
- sensitive export gating
- lifecycle hooks for retention/deletion workflows
- export-control API
- frontend export governance panel
- access and lifecycle tests

## Safety boundary

The system produces an authorization decision and auditable event. It does not silently
perform destructive deletion or export. Those actions remain explicit downstream operations
that must use the authorization result.
