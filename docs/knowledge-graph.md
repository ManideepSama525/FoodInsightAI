# Phase 8 — Knowledge Graph and Entity Resolution

## Purpose

The knowledge layer connects existing FoodInsightAI objects without replacing the RAG system.

Core entity types currently include:
- food
- nutrient
- recipe

The model is extensible to:
- ingredient
- hazard
- regulation
- source
- supplier
- trace event
- feedback topic

## Provenance

Entities and relationships carry `source_ids`. Relationship confidence is explicit.

The graph therefore does not imply that a relationship is authoritative merely because it exists.

## Entity resolution

Resolution currently uses deterministic normalization plus exact/substring matching.

Statuses:
- `resolved_exact`
- `candidate_matches`
- `ambiguous`
- `unresolved`

A production resolver should add identifiers, multilingual aliases, curated synonym tables,
and domain-specific disambiguation before automatically merging entities.

## Current implementation

The Phase 8 store is an in-memory development graph. It intentionally does not require Neo4j
or another graph database. The architecture can later map the same entity/relation models onto
Neo4j, PostgreSQL graph extensions, or another durable graph layer.

## API

- `GET /api/v1/knowledge/entities/{entity_id}`
- `GET /api/v1/knowledge/entities/{entity_id}/neighbors`
- `GET /api/v1/knowledge/resolve?q=...`
