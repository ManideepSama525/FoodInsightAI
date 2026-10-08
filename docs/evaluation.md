# Evaluation Methodology

### Retrieval
- Precision@K
- Recall@K
- context relevance

### Generation
- answer correctness
- faithfulness/groundedness
- citation correctness
- unsupported-claim/hallucination rate

### Domain modules
- nutrition numerical accuracy
- recipe constraint satisfaction
- safety agreement with reference labels
- regulatory retrieval correctness
- fraud precision/recall/F1 where labeled data exists

### System
- p50/p95 latency
- throughput
- error rate
- dependency failure behavior

All benchmark datasets must record provenance, version, licensing and whether examples are synthetic.
