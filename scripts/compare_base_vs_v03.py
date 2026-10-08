from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


SYSTEM = (
    "You are FoodInsight-LM, an evidence-aware food intelligence model. "
    "Use only supplied evidence for factual claims. "
    "If evidence is insufficient, say so explicitly. "
    "Preserve numeric values and units. "
    "Do not invent sources, nutrients, portions, or facts."
)


def build_messages(example: dict):
    user = (
        f"Question:\n{example['question']}\n\n"
        f"Evidence:\n{example.get('context', '')}\n\n"
        "Give a concise evidence-grounded answer."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]


def load_examples(path: Path, limit: int):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
            if limit and len(rows) >= limit:
                break
    return rows


def generate(model, tokenizer, messages, max_new_tokens=160):
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            repetition_penalty=1.0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    new_tokens = out[0, inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=False)


def stats(text: str, expected: str):
    clean = text.replace("\r", "")
    return {
        "nonempty": bool(clean.strip()),
        "expected_present": bool(expected and expected.strip() in clean),
        "expected_at_start": bool(expected and clean.lstrip().startswith(expected.strip())),
        "for_can_be_converted_count": clean.count("ForCanBeConverted"),
        "im_end_present": "<|im_end|>" in clean,
        "eos_present": "<|endoftext|>" in clean,
        "replacement_char_count": clean.count("�"),
        "chars": len(clean),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print("Loading base model...")
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quant,
        device_map="auto",
        trust_remote_code=True,
    )
    base.eval()

    print("Loading LoRA model...")
    lora = PeftModel.from_pretrained(base, args.adapter)
    lora.eval()

    rows = load_examples(Path(args.test), args.limit)
    results = []

    for i, ex in enumerate(rows):
        messages = build_messages(ex)
        expected = str(ex.get("answer", ""))

        base_text = generate(base, tokenizer, messages)
        lora_text = generate(lora, tokenizer, messages)

        item = {
            "index": i,
            "question": ex.get("question", ""),
            "expected_answer": expected,
            "base": {
                "prediction": base_text,
                "stats": stats(base_text, expected),
            },
            "v03_lora": {
                "prediction": lora_text,
                "stats": stats(lora_text, expected),
            },
        }
        results.append(item)

        print(f"[{i}] base={item['base']['stats']} lora={item['v03_lora']['stats']}")

    def aggregate(key):
        ss = [r[key]["stats"] for r in results]
        n = len(ss) or 1
        return {
            "examples": len(ss),
            "expected_present_rate": sum(x["expected_present"] for x in ss) / n,
            "expected_at_start_rate": sum(x["expected_at_start"] for x in ss) / n,
            "im_end_rate": sum(x["im_end_present"] for x in ss) / n,
            "eos_rate": sum(x["eos_present"] for x in ss) / n,
            "avg_for_can_be_converted": sum(x["for_can_be_converted_count"] for x in ss) / n,
            "avg_replacement_chars": sum(x["replacement_char_count"] for x in ss) / n,
            "avg_chars": sum(x["chars"] for x in ss) / n,
        }

    output = {
        "diagnostic": "Qwen3-1.7B base vs FoodInsight V0.3 QLoRA",
        "purpose": "Determine whether the ForCanBeConverted/repetition behavior is introduced by V0.3 fine-tuning.",
        "base_model": args.base_model,
        "adapter": args.adapter,
        "test": args.test,
        "limit": args.limit,
        "aggregate": {
            "base": aggregate("base"),
            "v03_lora": aggregate("v03_lora"),
        },
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
