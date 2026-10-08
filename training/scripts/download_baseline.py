from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download

MODEL_ID = os.getenv("MODEL_ID", "HuggingFaceTB/SmolLM2-360M-Instruct")
MODEL_DIR = Path(os.getenv("MODEL_DIR", "models/SmolLM2-360M-Instruct"))
REVISION = os.getenv("MODEL_REVISION") or None
TOKEN = os.getenv("HF_TOKEN") or None

MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("Model:", MODEL_ID)
print("Local directory:", MODEL_DIR)
print("Revision:", REVISION or "default")
print("Authenticated:", bool(TOKEN))

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=str(MODEL_DIR),
    revision=REVISION,
    token=TOKEN,
)

print("MODEL DOWNLOAD: OK")
