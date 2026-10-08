# Phase 9 — Hybrid Retrieval and Reasoning Context

FoodInsightAI now has an explicit integration boundary between retrieval and response generation.

## Channels

The unified retriever can accept:
- vector retrieval
- lexical retrieval
- knowledge-graph evidence
- structured nutrition/domain data

Each signal retains its source type, source ID, score, content, and metadata.

## Why merge channels?

Vector similarity is useful for semantic evidence. Lexical retrieval preserves exact terminology.
Graph retrieval exposes relationships. Structured data provides values that should not be invented by
an LLM.

The merger therefore creates a single evidence package while preserving each channel's provenance.

## Multimodal boundary

Visual observations remain separate from authoritative evidence. A vision model can say that an image
contains a possible object or visual characteristic, but that observation is not automatically treated as
a nutrition, safety, regulatory, or ingredient fact.

## Answer policy

The policy explicitly distinguishes:
- evidence-supported summaries
- structured nutrition values
- labeled observations

from:
- invented nutrition values
- unsupported regulatory claims
- unverified adulteration conclusions

## API

`POST /api/v1/reasoning/context`

This endpoint is a development integration boundary. The existing ChatService remains responsible for
LLM orchestration and grounding validation.
