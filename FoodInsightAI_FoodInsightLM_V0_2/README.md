# FoodInsight-LM V0.2 Training Pack

## Objective

Train a locally deployable, evidence-aware FoodInsight-LM from the Apache-2.0
Qwen3-1.7B base model using free/open datasets and QLoRA/SFT.

The training target is NOT a generic chatbot. It is a food-domain model that
learns:

- nutrition and food composition
- nutrient/portion reasoning
- evidence selection
- provenance
- uncertainty
- conflict detection
- unsupported-claim rejection
- grounded answer generation

The trained model remains one component of FoodInsightAI. Hybrid-RAG,
structured SQL/USDA retrieval, knowledge-graph reasoning, evidence fusion,
and the existing ClaimVerifier remain authoritative grounding layers.

## Research rule

Never train on the final test set.

The split is food/entity-level, not question-level.

## Base model

Qwen/Qwen3-1.7B (Apache-2.0).

## Training sequence

1. Acquire/prepare USDA data.
2. Build FoodInsight dataset V0.2.
3. Run dataset quality gates.
4. Run QLoRA/SFT in Colab.
5. Evaluate on the locked test set.
6. Mine failure modes.
7. Improve the training mixture.
8. Run a second training iteration only if validation evidence supports it.
9. Integrate the best adapter into FoodInsightAI.
10. Run end-to-end Hybrid-RAG + verification evaluation.

## Important

This pack deliberately does NOT claim that training has already happened.
A model checkpoint is only considered trained after a reproducible training
run produces an artifact and the independent evaluation passes.
