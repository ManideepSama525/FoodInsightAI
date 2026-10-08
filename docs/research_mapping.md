# Research → Engineering Mapping

The project specification identifies food-science LLM directions including food safety, regulation, inspection/quality, consumer feedback, supply-chain traceability, food fraud, recipe generation and nutrition. It also emphasizes hallucination, outdated knowledge, domain terminology, data quality, privacy, interoperability, multimodality and validation.

| Research concern | Engineering response | Evaluation |
|---|---|---|
| Predictive/food safety | Safety knowledge service + retrieval + validation | reference agreement |
| Regulatory compliance | jurisdiction-aware regulatory retrieval | retrieval/citation correctness |
| Food inspection/quality | vision observations + criteria retrieval | uncertainty + agreement |
| Consumer feedback | structured sentiment/topic analysis | label agreement |
| Supply chain | relational records + optional Neo4j graph | path/query correctness |
| Food fraud | signal/risk-analysis module | precision/recall/F1 where labels exist |
| Recipe generation | constrained structured generation + retrieved nutrition | constraint satisfaction |
| Nutrition | structured data retrieval, not LLM arithmetic | numerical accuracy |
| Outdated knowledge | versioned, rebuildable ingestion | freshness/provenance audit |
| Hallucination | RAG + relevance checks + citation validation | unsupported-claim rate |
| Multimodal limitation | vision and document preprocessing before retrieval | multimodal task accuracy |
| Trust | source attribution + warnings + evaluation | citation correctness |

The supplied research foundation is treated as a conceptual foundation, not as evidence that it implemented FoodInsightAI.
