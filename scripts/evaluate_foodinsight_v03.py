#!/usr/bin/env python3
"""
FoodInsight-LM V0.3 held-out evaluation.

Evaluates the trained QLoRA adapter on the untouched V0.3 test set.
This script is intentionally separate from training so the test set cannot
accidentally be loaded into the training loop.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base-model", required=True)
    p.add_argument("--adapter", required=True)
    p.add_argument("--test", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--limit", type=int, default=0,
                   help="0 evaluates the complete held-out test set.")
    return p.parse_args()


def load_model(base_model: str, adapter: str):
    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quant,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return tokenizer, model


def extract_text(example):
    # Support the JSONL schemas used by our FoodInsight dataset builder.
    for key in ("output", "response", "answer", "assistant"):
        if isinstance(example.get(key), str):
            return example[key]
    messages = example.get("messages")
    if isinstance(messages, list):
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "assistant":
                return str(m.get("content", ""))
    return ""


def extract_prompt(example):
    for key in ("prompt", "instruction", "question", "input"):
        if isinstance(example.get(key), str):
            return example[key]
    messages = example.get("messages")
    if isinstance(messages, list):
        parts = []
        for m in messages:
            if isinstance(m, dict) and m.get("role") == "user":
                parts.append(str(m.get("content", "")))
        if parts:
            return "\n".join(parts)
    return ""


def main():
    args = parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    tokenizer, model = load_model(args.base_model, args.adapter)
    ds = load_dataset("json", data_files=args.test, split="train")
    if args.limit:
        ds = ds.select(range(min(args.limit, len(ds))))

    records = []
    total = len(ds)

    for i, example in enumerate(ds):
        prompt = extract_prompt(example)
        expected = extract_text(example)

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        new_tokens = generated[0][inputs["input_ids"].shape[1]:]
        prediction = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        records.append({
            "index": i,
            "prompt": prompt,
            "expected": expected,
            "prediction": prediction,
        })

        if (i + 1) % 100 == 0 or i + 1 == total:
            print(f"Evaluated {i + 1}/{total}")

    # Lightweight deterministic metrics. These are diagnostics, not a claim of
    # semantic quality; the full benchmark will add task-specific scorers.
    exact = 0
    nonempty = 0
    for r in records:
        pred = r["prediction"].strip()
        exp = r["expected"].strip()
        if pred:
            nonempty += 1
        if pred.lower() == exp.lower() and exp:
            exact += 1

    result = {
        "model": "FoodInsight-LM V0.3 QLoRA",
        "base_model": args.base_model,
        "adapter": args.adapter,
        "test_examples": total,
        "exact_match": exact / total if total else 0.0,
        "nonempty_rate": nonempty / total if total else 0.0,
        "note": "Held-out generation diagnostics. Exact match alone is not a sufficient quality metric.",
        "samples": records[:50],
    }
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))


if __name__ == "__main__":
    main()
