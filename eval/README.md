# FoodInsightAI Evaluation

Phase 10 introduces a deterministic evaluation harness.

## Dimensions

- Retrieval recall@k
- answer token overlap
- citation coverage
- recipe/constraint satisfaction
- multimodal uncertainty handling
- entity resolution

The harness is intentionally modular. Future benchmark adapters can add:
- expert-annotated food QA
- multilingual cases
- adversarial prompt-injection cases
- nutrition arithmetic suites
- regulatory evidence suites
- image-grounded cases
- latency/cost measurements

## Important

The included cases are smoke-test fixtures, not a scientific benchmark and not a claim of
production performance. Real evaluation requires representative, independently curated datasets
and clearly defined annotation protocols.
