# Phase 31 — API Contract & Capability Discovery

Phase 31 makes the production API contract explicit and machine-readable.

## Added

- API contract metadata
- stable version declaration
- supported/deprecated version lists
- capability discovery
- `X-FoodInsight-API-Version` response header
- contract endpoint
- frontend capability-discovery panel
- contract tests

## Endpoint

`GET /api/v1/system/contract`

The contract describes the public application surface without exposing implementation details.
Future API versions can be introduced with explicit compatibility and deprecation metadata.
