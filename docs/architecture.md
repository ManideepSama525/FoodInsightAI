# FoodInsightAI Architecture

## 1. System flow

```text
Text / Image / PDF / Multiple Inputs
              |
              v
       Input Validation
              |
      +-------+--------+
      |                |
    Image            Document
      |                |
 VisionProvider   Parser + OCR
      |                |
      +-------+--------+
              v
       Content Normalizer
              |
              v
       Query Understanding
              |
      +-------+--------+
      |                |
 Vector Retrieval   Graph Retrieval
      |                |
      +-------+--------+
              v
        Reranking
              |
              v
        Context Builder
              |
              v
          LLMService
              |
              v
      Domain Validation
              |
              v
   Answer + Sources + Warnings
```

Image understanding happens before retrieval. RAG retrieves textual/structured evidence; it is not the image-understanding component.

## 2. Separation of concerns

- **Model layer:** pretrained/API LLM, vision, and embedding providers.
- **RAG layer:** parsing, chunking, embedding, vector retrieval, reranking, context construction, citations.
- **Knowledge base:** curated food documents and structured datasets with provenance.
- **Domain logic:** nutrition, safety, recipe, regulatory, fraud, feedback, traceability.
- **Application:** REST API, UI, authentication, persistence, observability.

## 3. Retrieval strategy

Vector search is the default for semantic document evidence. PostgreSQL is the source of truth for application/structured records. Neo4j is optional and used for relationship-heavy traceability and food-ingredient-regulation queries.

## 4. Grounding strategy

The LLM receives only selected evidence plus explicit instructions not to treat retrieved content as instructions. The response contract includes citations, warnings, and an insufficient-evidence path. Hidden chain-of-thought is never returned.

## 5. Local-first strategy

Mock LLM and vision providers permit development without API credentials. Qdrant and PostgreSQL run locally through Docker. Neo4j is an optional Docker Compose profile because not every deployment needs graph retrieval.
