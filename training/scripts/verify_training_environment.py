from __future__ import annotations

import importlib
import sys

print("Python:", sys.version)

required = [
    "torch",
    "transformers",
    "accelerate",
    "datasets",
    "peft",
    "safetensors",
    "huggingface_hub",
]

for name in required:
    importlib.import_module(name)
    print(f"{name}: OK")

import torch

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if not torch.cuda.is_available():
    raise SystemExit(
        "CUDA is not available. Fix the PyTorch/CUDA environment before training."
    )

print("CUDA runtime:", torch.version.cuda)
print("GPU:", torch.cuda.get_device_name(0))

props = torch.cuda.get_device_properties(0)
print("VRAM GiB:", round(props.total_memory / 1024**3, 2))

x = torch.randn((1024, 1024), device="cuda", dtype=torch.float16)
y = x @ x
torch.cuda.synchronize()

print("GPU computation: OK")
print("Result checksum:", float(y.mean().item()))
