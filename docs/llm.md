# LLM Orchestration

## Provider abstraction

`LLMProvider` separates model access from application logic.

Phase 4 includes:
- `MockLLMProvider`
- provider factory
- centralized prompt loading
- structured response validation
- grounding validation
- citation resolution

A real provider adapter can implement the same `generate()` contract without changing `ChatService`.

## Prompt security

Retrieved documents are placed in a clearly delimited evidence section and explicitly labeled as untrusted data. They cannot override system instructions.

## Grounding

The validation layer:
- rejects malformed model output
- detects invalid source indexes
- detects absent citations
- handles missing evidence
- performs a conservative numeric-claim heuristic

The numeric heuristic is only a safety signal; it is not claimed to be a complete hallucination detector.

## No chain-of-thought

The API exposes the answer and evidence metadata, not hidden model reasoning.
