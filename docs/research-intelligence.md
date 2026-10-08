# FoodInsightAI Research Intelligence Layer

This layer is the first implementation of the revised research architecture.

## Components

1. **AdaptiveRetrievalRouter**
   - Selects/weights Vector, Structured SQL, Graph, and lexical retrieval.
   - v0 is deterministic and explainable.
   - The interface is intentionally replaceable by a trained routing model.

2. **EvidenceReliabilityScorer**
   - Combines relevance, source authority, freshness, and cross-source consistency.
   - Produces bounded reliability scores and provenance.

3. **ConflictDetector**
   - Conservatively identifies potential numerical and serving-size conflicts.
   - It flags conflicts rather than deciding which source is correct.

4. **EvidenceFusionEngine**
   - Applies reliability-aware reranking.
   - Penalizes evidence involved in detected conflicts.
   - Produces a compact evidence package.

5. **ClaimVerifier**
   - Baseline lexical claim/evidence verification.
   - Numeric claims receive stricter handling.
   - The verifier can later be replaced by a trained verifier without changing its API contract.

## API

- `POST /api/v1/research-intelligence/plan`
- `POST /api/v1/research-intelligence/analyze-evidence`
- `POST /api/v1/research-intelligence/verify`

## Research status

This is a **baseline implementation**, not a claim that the final learned models already exist.

The next research step is to create labeled training/evaluation data from these outputs and replace the deterministic router/reliability/verifier with learned models where experiments show an advantage.

## Core hypothesis

Adaptive source selection + reliability-aware evidence fusion + conflict detection + claim-level verification should reduce unsupported claims and improve grounded answer quality compared with basic hybrid retrieval.


## Real retrieval integration

`ResearchRetrievalService` now connects the router to the existing:
- `RAGPipeline` for document/vector evidence,
- `NutritionService` for structured food evidence,
- `KnowledgeGraphStore` for graph evidence.

New endpoint:
- `POST /api/v1/research-intelligence/retrieve-and-fuse`

The integration is intentionally fault-tolerant: if the document/vector store is unavailable, structured and graph retrieval can still return evidence and a warning is emitted.
