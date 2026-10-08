# Phase 11 — Production Data Layer and Persistence

Phase 11 adds durable PostgreSQL models and Alembic migration coverage for the remaining
development-state domain objects.

## Persistent domains

- foods and nutrients
- food nutrient measurements
- recipes and recipe ingredients
- safety evidence
- traceability events
- consumer feedback
- knowledge graph entities and relations
- evaluation runs

## Repository boundary

`app.repositories.persistence` provides asynchronous repository primitives over SQLAlchemy's
existing `AsyncSession`. Domain services can adopt these repositories incrementally without
coupling business logic to database statements.

## Migration

The migration is:

`0002_phase11_persistence`

It follows the existing `0001_initial` migration.

## Important distinction

Phase 11 establishes durable schema and repository infrastructure. The existing demo/in-memory
services remain available for local development. A production deployment should wire the domain
services to these repositories and configure PostgreSQL migrations as part of deployment.

## Data provenance

Food records retain source and synthetic status. Safety evidence retains source, source type,
confidence, jurisdiction, and effective date. Knowledge relationships retain source IDs and
confidence. Evaluation reports retain their metric and case results.
