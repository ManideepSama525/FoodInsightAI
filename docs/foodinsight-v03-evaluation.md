# FoodInsight-LM V0.3 Evaluation

The V0.3 QLoRA training run is complete. The next experiment is a held-out
evaluation using the untouched V0.3 test split.

## Rules

1. The test set must never enter the training loop.
2. The adapter is evaluated against the frozen base model.
3. Exact match is only a diagnostic.
4. Numeric claims receive a separate diagnostic.
5. The final research comparison should include the full FoodInsight pipeline,
   not only the language model.

## Execution

Use `scripts/evaluate_foodinsight_v03.py` with the local base-model path,
adapter output path, and V0.3 test JSONL path.

The output JSON stores a small sample of predictions for qualitative review.
