# FoodInsightAI Model Layer

## Current decision

FoodInsightAI now has an optional **local open-weight Transformers provider**.

We deliberately do not hard-code a specific model family. Model selection is an
experimental decision based on:
- available GPU memory,
- inference latency,
- answer quality,
- grounding/verification performance,
- licensing/usage rights,
- and training feasibility.

## Local execution

The backend can run without ML dependencies. To enable a local model:

1. Install `backend/requirements-local-model.txt`.
2. Set a valid open-weight model ID or local model directory.
3. Run the local benchmark.
4. Record hardware and quality metrics.

## Research/Colab workflow

`research/notebooks/foodinsight_model_lab_v1.ipynb` is the initial notebook for:
- GPU diagnostics,
- candidate-model benchmarking,
- training-pilot preparation,
- reproducible experiment logging.

The final model choice should not be made from parameter count alone.

## Training direction

If experiments support it, the project can evaluate:
- pretrained local inference as the baseline,
- parameter-efficient adaptation,
- and a compact FoodInsight model trained from scratch.

The architecture around the model remains the main system contribution:
adaptive routing, evidence reliability, conflict detection, evidence fusion,
claim verification, and bounded verification feedback.
