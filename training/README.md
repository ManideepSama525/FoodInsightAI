# FoodInsightAI — Ready-to-Build Handoff

This archive is the consolidated FoodInsightAI project based on the model-layer-v1 project snapshot, with the latest cursor-reactive frontend visual layer integrated.

## What you do

Only two research inputs are intentionally left to you:

1. **Download/prepare the USDA Foundation Foods dataset**
   - Run `training\scripts\download_and_prepare_usda.cmd`
   - The script downloads the official public USDA release and creates leakage-controlled food-level train/validation/test tasks.

2. **Run model training**
   - Run `training\scripts\train.cmd`
   - Default: SmolLM2-360M-Instruct + LoRA on the local NVIDIA GPU.

Everything else needed for the application build is included.

## Build the application

From this directory:

```cmd
SETUP_FOODINSIGHTAI.cmd
docker compose build
docker compose up
```

Frontend:
`http://localhost:3000`

Backend:
`http://localhost:8000`

## Credentials

The default Docker Compose configuration uses local development credentials for PostgreSQL/Qdrant and mock LLM/vision providers.

No paid API key is required for the default path.

Do NOT put credentials into Dockerfiles.

If a future private Hugging Face model is used, put `HF_TOKEN` in an ignored `.env` or environment variable only.

## Model path

```text
training/
  scripts/
    download_and_prepare_usda.py
    train_foodinsight_lora.py
    evaluate_foodinsight_model.py
  requirements-model-training.txt
```

## Research note

The USDA generator deliberately uses food-level split isolation so records for the same food do not leak across train/validation/test. This is a stronger starting point than the earlier task-level V0.1 split.

The model is not the sole source of truth. The FoodInsightAI retrieval, evidence reliability, conflict detection, evidence fusion and claim verification layers remain part of the system.
