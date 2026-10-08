from __future__ import annotations

import argparse
import json
import re
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


def load_rows(path, limit):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
                if limit and len(rows) >= limit:
                    break
    return rows


def user_text(ex):
    return (
        f"Question:\n{ex['question']}\n\n"
        f"Evidence:\n{ex.get('context', '')}\n\n"
        "Give a concise evidence-grounded answer."
    )


def build_prompt(ex, mode):
    u = user_text(ex)
    if mode == "raw":
        return f"System:\n{SYSTEM}\n\nUser:\n{u}\n\nAssistant:\n"
    if mode == "direct":
        return (
            "FoodInsight-LM\n"
            "Answer the following using only the supplied evidence. "
            "Return one concise answer and stop.\n\n"
            f"{u}\n\n"
            "Answer:"
        )
    raise ValueError(mode)


def generate(model, tok, prompt, max_new_tokens):
    enc = tok(prompt, return_tensors="pt")
    enc = {k: v.to(model.device) for k, v in enc.items()}
    with torch.inference_mode():
        out = model.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            repetition_penalty=1.0,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    n = enc["input_ids"].shape[1]
    ids = out[0, n:].detach().cpu().tolist()
    return ids, tok.decode(ids, skip_special_tokens=False)


def numbers(s):
    return re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", s or "")


def stats(text, expected):
    t = text.strip()
    exp = str(expected).strip()
    return {
        "nonempty": bool(t),
        "expected_present": bool(exp and exp in text),
        "expected_at_start": bool(exp and t.startswith(exp)),
        "for_can_be_converted_count": text.count("ForCanBeConverted"),
        "im_end_present": "<|im_end|>" in text,
        "eos_present": "<|endoftext|>" in text,
        "replacement_chars": text.count("�"),
        "chars": len(text),
        "numbers_in_prediction": numbers(text),
        "numbers_in_expected": numbers(exp),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--mode", choices=["raw", "direct", "both"], default="both")
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print("Loading base...")
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quant,
        device_map="auto",
        trust_remote_code=True,
    ).eval()

    print("Loading V0.3 LoRA...")
    lora = PeftModel.from_pretrained(base, args.adapter).eval()

    rows = load_rows(args.test, args.limit)
    modes = ["raw", "direct"] if args.mode == "both" else [args.mode]
    results = []

    for i, ex in enumerate(rows):
        item = {
            "index": i,
            "question": ex.get("question", ""),
            "expected_answer": ex.get("answer", ""),
            "modes": {},
        }

        for mode in modes:
            prompt = build_prompt(ex, mode)
            base_ids, base_text = generate(base, tok, prompt, args.max_new_tokens)
            lora_ids, lora_text = generate(lora, tok, prompt, args.max_new_tokens)

            item["modes"][mode] = {
                "prompt": prompt,
                "base": {
                    "prediction": base_text,
                    "stats": stats(base_text, ex.get("answer", "")),
                },
                "v03_lora": {
                    "prediction": lora_text,
                    "stats": stats(lora_text, ex.get("answer", "")),
                },
                "base_lora_tokens_identical": base_ids == lora_ids,
            }

        results.append(item)
        print(
            f"[{i}] "
            + " ".join(
                f"{m}:loop={item['modes'][m]['v03_lora']['stats']['for_can_be_converted_count']} "
                f"expected={item['modes'][m]['v03_lora']['stats']['expected_present']}"
                for m in modes
            )
        )

    aggregate = {}
    for mode in modes:
        for model_key in ["base", "v03_lora"]:
            ss = [r["modes"][mode][model_key]["stats"] for r in results]
            n = len(ss) or 1
            aggregate[f"{mode}_{model_key}"] = {
                "examples": len(ss),
                "expected_present_rate": sum(x["expected_present"] for x in ss) / n,
                "expected_at_start_rate": sum(x["expected_at_start"] for x in ss) / n,
                "nonempty_rate": sum(x["nonempty"] for x in ss) / n,
                "avg_loop_count": sum(x["for_can_be_converted_count"] for x in ss) / n,
                "zero_loop_rate": sum(x["for_can_be_converted_count"] == 0 for x in ss) / n,
                "im_end_rate": sum(x["im_end_present"] for x in ss) / n,
                "replacement_char_rate": sum(x["replacement_chars"] > 0 for x in ss) / n,
                "avg_chars": sum(x["chars"] for x in ss) / n,
            }

    output = {
        "diagnostic": "FoodInsight V0.4 raw/direct inference evaluation",
        "purpose": "Evaluate whether bypassing the Qwen3 chat-template/reasoning path produces clean, evidence-grounded generation.",
        "limit": args.limit,
        "max_new_tokens": args.max_new_tokens,
        "aggregate": aggregate,
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
