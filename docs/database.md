# Database Design

PostgreSQL is the application source of truth.

Core entities:
- users
- documents
- document_chunks
- foods
- ingredients
- nutrients
- recipes
- food_safety_records
- regulations
- products
- suppliers
- traceability_records
- feedback
- queries
- responses
- citations

Phase 1 creates the foundational document/chunk/query entities. Remaining domain entities are added with migrations as their services are implemented.

Qdrant stores embeddings plus payload metadata such as document ID, chunk ID, page, source, jurisdiction and dataset version.

Neo4j stores relationship-heavy entities and edges only when graph traversal adds value.
