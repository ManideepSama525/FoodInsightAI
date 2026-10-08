# FoodInsightAI — Model Training Bundle

This bundle is the **model-training/setup slice** of FoodInsightAI.

It is designed for the current local development machine:

- Windows 11 x64
- Python 3.12
- NVIDIA RTX 4050 Laptop GPU (~6 GB VRAM)
- CUDA-capable PyTorch
- Existing FoodInsightAI project at `C:\Users\manid\fi34`

## What this bundle does

1. Creates/uses a project-local Python training environment.
2. Installs only the dependencies needed for local model training/evaluation.
3. Verifies PyTorch + CUDA.
4. Downloads the public `HuggingFaceTB/SmolLM2-360M-Instruct` baseline locally.
5. Trains a FoodInsightAI domain adapter with LoRA by default.
6. Evaluates the trained model on the supplied benchmark schema.
7. Keeps Hugging Face credentials optional.
8. Keeps secrets out of Dockerfiles and source control.
9. Provides an optional Docker training definition; native Windows/WSL2 training is the recommended first path for this machine.

## Important research boundary

The dataset generator and benchmark included here are research artifacts. The previously created USDA V0.1 corpus should **not** be treated as the final leakage-controlled research corpus. The final training corpus should use food-level split isolation and balanced task families.

The architecture remains:

UNDERSTAND → RETRIEVE → REASON → VALIDATE → RESPOND

The trained model is not the sole source of truth. FoodInsightAI's retrieval, evidence reliability, conflict detection, evidence fusion, and claim verification layers remain part of the system.

## Default training choice

The default is **LoRA fine-tuning of SmolLM2-360M-Instruct**.

Why:

- low VRAM requirement
- fast iteration on the RTX 4050
- reproducible
- does not destroy the original pretrained checkpoint
- produces a small adapter
- appropriate for an academic research baseline

This is not a claim that LoRA is the final research model. It is the safe first training experiment.

## Credentials

A public SmolLM2 download does not require a Hugging Face token.

If a future private/gated model requires one:

- put it in `.env`
- never put it in a Dockerfile
- never commit `.env`
- never paste the token into source code

See `.env.example`.

## Quick start

From the existing FoodInsightAI project:

```cmd
cd C:\Users\manid\fi34
training\scripts\setup_model_training.cmd
```

Then:

```cmd
training\scripts\download_baseline.cmd
```

Then prepare/verify the dataset:

```cmd
training\scripts\prepare_dataset.cmd
```

Then train:

```cmd
training\scripts\train.cmd
```

Then evaluate:

```cmd
training\scripts\evaluate.cmd
```

The commands are intentionally Windows CMD-friendly.

## Expected outputs

```text
models/
  SmolLM2-360M-Instruct/

research/
  dataset/
    foodinsight_lm/
  evaluation/
    model_benchmark_results.json

artifacts/
  foodinsight_lora/
```

## What is NOT included

This bundle does not pretend to contain the user's complete private/local source tree. The Windows project at `C:\Users\manid\fi34` cannot be read from this chat runtime.

Instead, this archive is a drop-in training package that operates on the existing project and does not overwrite the backend/frontend.

The existing model layer already supports a local Transformers provider and benchmark infrastructure. This bundle adds the practical training execution path around it.
