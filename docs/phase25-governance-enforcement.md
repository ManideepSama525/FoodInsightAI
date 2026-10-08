# Phase 25 — Governance Enforcement

Phase 25 moves privacy controls from documentation into enforceable policy primitives.

## Added

- data classification: public, internal, sensitive, restricted
- access context with purpose and consent
- deterministic policy decisions
- immutable-style audit record model
- retention cleanup planning
- policy-check API
- frontend governance check panel

## Design

Sensitive data requires explicit consent unless an authorized administrative context is used.
Restricted data follows the same boundary. Policy decisions produce an audit identifier without
logging the underlying sensitive payload.

The retention planner remains a planning primitive; destructive deletion should be executed
transactionally by repository-specific jobs after authorization.
