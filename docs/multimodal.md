# Multimodal Architecture

## Image pipeline

```text
image upload
   ↓
file validation
   ↓
EXIF-safe normalization
   ↓
VisionProvider
   ↓
FoodObservation
   ↓
retrieval query
   ↓
RAG
   ↓
LLM
   ↓
grounding validation
```

### Critical separation

Vision output is an **observation**, not authoritative food knowledge.

For example, a vision model may suggest:
- food candidate
- visible ingredients
- preparation characteristics
- visual observations

The system must retrieve nutritional, safety, regulatory or scientific information from the knowledge base instead of inventing exact values from pixels.

### Uncertainty

Every observation has:
- confidence
- uncertainty
- warnings

A low-confidence observation must not be silently presented as certain identification.

### Provider abstraction

`VisionProvider` is independent of the rest of the application. The local mock provider permits development without credentials. A production vision-capable API/model can implement the same interface.

### Multimodal RAG

The image itself is processed before retrieval. RAG receives normalized textual observations and the user's question. This preserves the architectural distinction between **perception** and **retrieval**.
