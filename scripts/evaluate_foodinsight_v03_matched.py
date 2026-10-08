#!/usr/bin/env python3
"""
FoodInsight-LM V0.3 held-out evaluation — TRAINING-FORMAT MATCHED.

Important:
The original evaluator passed only the raw question to the model.
V0.3 training actually used:
  system instruction + question + evidence + generation prompt
through the tokenizer chat template.

This evaluator reproduces the V0.3 training/inference prompt format.
It does NOT retrain the model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


SYSTEM = (
    "You are FoodInsight-LM, an evidence-aware food intelligence model. "
    "Use only supplied evidence for factual claims. "
    "If evidence is insufficient, say so explicitly. "
    "Preserve numeric values and units. "
    "Do not invent sources, nutrients, portions, or facts."
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base-model", required=True)
    p.add_argument("--adapter", required=True)
    p.add_argument("--test", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--max-new-tokens", type=int, default=128)
    p.add_argument("--limit", type=int, default=50)
    return p.parse_args()


def load_model(base_model: str, adapter: str):
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=dtype,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        trust_remote_code=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quant,
        device_map="auto",
        trust_remote_code=True,
    )

    model = PeftModel.from_pretrained(model, adapter)
    model.eval()

    return tokenizer, model


def build_prompt(tokenizer, example: dict) -> str:
    """
    EXACTLY mirrors the prompt construction in train_foodinsight_qlora_v03.py.
    """
    user = (
        f"Question:\n{example['question']}\n\n"
        f"Evidence:\n{example.get('context', '')}\n\n"
        "Give a concise evidence-grounded answer."
    )

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]

    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return f"System:\n{SYSTEM}\n\nUser:\n{user}\n\nAssistant:\n"


def extract_expected(example: dict) -> str:
    value = example.get("answer")
    if isinstance(value, str):
        return value

    for key in ("output", "response", "assistant"):
        value = example.get(key)
        if isinstance(value, str):
            return value

    return ""


def main():
    args = parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    tokenizer, model = load_model(
        args.base_model,
        args.adapter,
    )

    ds = load_dataset(
        "json",
        data_files=args.test,
        split="train",
    )

    limit = min(args.limit, len(ds)) if args.limit > 0 else len(ds)
    ds = ds.select(range(limit))

    records = []

    for i, example in enumerate(ds):
        prompt = build_prompt(tokenizer, example)
        expected = extract_expected(example)

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            add_special_tokens=False,
        ).to(model.device)

        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                num_beams=1,
                pad_token_id=(
                    tokenizer.pad_token_id
                    if tokenizer.pad_token_id is not None
                    else tokenizer.eos_token_id
                ),
                eos_token_id=tokenizer.eos_token_id,
            )

        new_tokens = generated[0][inputs["input_ids"].shape[1]:]

        prediction = tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()

        records.append(
            {
                "index": i,
                "question": example.get("question", ""),
                "context_chars": len(str(example.get("context", ""))),
                "expected": expected,
                "prediction": prediction,
            }
        )

        if (i + 1) % 10 == 0 or i + 1 == limit:
            print(f"Evaluated {i + 1}/{limit}")

    exact = 0
    nonempty = 0

    for record in records:
        pred = record["prediction"].strip()
        exp = record["expected"].strip()

        if pred:
            nonempty += 1

        if pred.lower() == exp.lower() and exp:
            exact += 1

    result = {
        "model": "FoodInsight-LM V0.3 QLoRA",
        "base_model": args.base_model,
        "adapter": args.adapter,
        "test_examples": len(records),
        "exact_match": exact / len(records) if records else 0.0,
        "nonempty_rate": nonempty / len(records) if records else 0.0,
        "prompt_format": "V0.3 training-format matched",
        "critical_fix": (
            "Evaluation now supplies the same system instruction, "
            "question, evidence, and chat-template generation prompt "
            "used during V0.3 training."
        ),
        "note": (
            "Exact match is still not a sufficient quality metric. "
            "Use the FoodInsight claim/numeric/unit/provenance evaluator "
            "after this smoke test."
        ),
        "samples": records,
    }

    out.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(
        {k: v for k, v in result.items() if k != "samples"},
        indent=2,
    ))


if __name__ == "__main__":
    main()
