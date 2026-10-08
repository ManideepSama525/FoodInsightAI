# FoodInsightAI Training Runbook

## A. One-time setup

```cmd
cd C:\Users\manid\fi34
training\scripts\setup_model_training.cmd
```

This installs the training dependencies into `.venv`.

## B. Download baseline

```cmd
training\scripts\download_baseline.cmd
```

Expected:

```text
models\SmolLM2-360M-Instruct
```

## C. Prepare dataset

Place the final training JSONL under:

```text
research\dataset\foodinsight_lm\
```

Preferred:

```text
foodinsight_usda_v0_2.jsonl
```

Then:

```cmd
training\scripts\prepare_dataset.cmd
```

## D. Train

```cmd
training\scripts\train.cmd
```

Default settings are intentionally conservative for an RTX 4050 Laptop GPU:

- batch size 1
- gradient accumulation 8
- max sequence length 512
- 2 epochs
- LoRA
- fp16

If VRAM is insufficient, reduce `MAX_SEQ_LENGTH` to 384 before changing anything else.

## E. Evaluate

```cmd
training\scripts\evaluate.cmd
```

Result:

```text
research\evaluation\model_benchmark_results.json
```

## F. Hugging Face credentials

Public models require no token.

For a gated/private model:

```text
HF_TOKEN=your_token_here
```

in `.env`.

Never put the token in:

- Dockerfile
- docker-compose.yml
- Python source
- Git
- README
- screenshots

## G. Docker

Training on the existing Windows host is recommended first because CUDA is already verified there.

The optional Docker training definition is included for reproducibility. It expects the NVIDIA Container Toolkit/WSL2 GPU path to be configured separately.

No credentials are baked into the Docker image.
