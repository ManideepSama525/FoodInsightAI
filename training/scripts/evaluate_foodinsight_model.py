from __future__ import annotations

import json
import os
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / os.getenv("MODEL_DIR", "models/SmolLM2-360M-Instruct")
ADAPTER_DIR = ROOT / os.getenv("TRAIN_OUTPUT_DIR", "artifacts/foodinsight_lora")
DATASET = ROOT / "research/evaluation/benchmark_questions.json"
OUTPUT = ROOT / os.getenv(
    "EVAL_OUTPUT",
    "research/evaluation/model_benchmark_results.json",
)


def build_prompt(tokenizer, item):
    messages = [
        {
            "role": "system",
            "content": (
                "You are FoodInsightAI, an evidence-aware food intelligence "
                "assistant. Answer only from the supplied evidence. Do not invent facts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{item['question']}\n\n"
                f"Evidence:\n"
                + "\n".join(f"- {x}" for x in item["evidence"])
                + "\n\nGive a concise answer."
            ),
        },
    ]

    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return (
        messages[0]["content"]
        + "\n\n"
        + messages[1]["content"]
        + "\n\nAssistant:\n"
    )


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for evaluation.")

    dataset = json.loads(DATASET.read_text(encoding="utf-8"))

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_DIR),
        torch_dtype=torch.float16,
    )

    if ADAPTER_DIR.exists() and (ADAPTER_DIR / "adapter_config.json").exists():
        model = PeftModel.from_pretrained(model, str(ADAPTER_DIR))
        print("Loaded LoRA adapter:", ADAPTER_DIR)
    else:
        print("No LoRA adapter found; evaluating base model.")

    model = model.to("cuda")
    model.eval()

    results = []
    total_generated = 0
    total_seconds = 0.0

    for item in dataset:
        prompt = build_prompt(tokenizer, item)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()

        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=80,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start

        generated = output.shape[1] - inputs["input_ids"].shape[1]
        answer = tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()

        total_generated += generated
        total_seconds += elapsed

        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": answer,
                "generation": {
                    "generated_tokens": generated,
                    "latency_seconds": round(elapsed, 4),
                    "tokens_per_second": round(
                        generated / elapsed if elapsed else 0,
                        3,
                    ),
                    "peak_vram_gib": round(
                        torch.cuda.max_memory_allocated() / 1024**3,
                        3,
                    ),
                },
            }
        )

    summary = {
        "model_dir": str(MODEL_DIR),
        "adapter_dir": str(ADAPTER_DIR) if ADAPTER_DIR.exists() else None,
        "gpu": torch.cuda.get_device_name(0),
        "questions": len(results),
        "average_latency_seconds": round(
            total_seconds / len(results), 4
        ) if results else 0,
        "average_tokens_per_second": round(
            total_generated / total_seconds, 3
        ) if total_seconds else 0,
        "results": results,
        "note": (
            "This benchmark measures generation behavior. It is not a "
            "complete factual-correctness evaluation."
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print("EVALUATION COMPLETE")


if __name__ == "__main__":
    main()
