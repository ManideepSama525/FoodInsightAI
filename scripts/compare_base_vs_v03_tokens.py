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


def messages_for(ex):
    user = (
        f"Question:\n{ex['question']}\n\n"
        f"Evidence:\n{ex.get('context', '')}\n\n"
        "Give a concise evidence-grounded answer."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]


def load_rows(path, limit):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
                if limit and len(rows) >= limit:
                    break
    return rows


def generate(model, tok, messages, max_new_tokens):
    prompt = tok.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
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
            return_dict_in_generate=True,
            output_scores=False,
        )

    prompt_len = enc["input_ids"].shape[1]
    ids = out.sequences[0, prompt_len:].detach().cpu().tolist()
    text = tok.decode(ids, skip_special_tokens=False)
    return ids, text, prompt


def token_view(tok, ids):
    return [
        {
            "position": i,
            "id": tid,
            "token": tok.convert_ids_to_tokens(tid),
            "decoded": tok.decode([tid], skip_special_tokens=False),
        }
        for i, tid in enumerate(ids)
    ]


def first_diff(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    print("Tokenizer diagnostics:")
    print("  eos:", repr(tok.eos_token), tok.eos_token_id)
    print("  pad:", repr(tok.pad_token), tok.pad_token_id)
    for special in ["<|im_end|>", "<|im_start|>", "<think>", "</think>"]:
        ids = tok.encode(special, add_special_tokens=False)
        print(f"  {special}: {ids}")

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

    print("Loading LoRA...")
    lora = PeftModel.from_pretrained(base, args.adapter).eval()

    rows = load_rows(args.test, args.limit)
    results = []

    for i, ex in enumerate(rows):
        messages = messages_for(ex)
        base_ids, base_text, prompt = generate(base, tok, messages, args.max_new_tokens)
        lora_ids, lora_text, _ = generate(lora, tok, messages, args.max_new_tokens)

        diff = first_diff(base_ids, lora_ids)

        item = {
            "index": i,
            "question": ex.get("question", ""),
            "expected_answer": ex.get("answer", ""),
            "prompt": prompt,
            "base": {
                "token_count": len(base_ids),
                "token_ids": base_ids,
                "text": base_text,
            },
            "v03_lora": {
                "token_count": len(lora_ids),
                "token_ids": lora_ids,
                "text": lora_text,
            },
            "token_sequences_identical": base_ids == lora_ids,
            "first_token_difference": diff,
            "base_token_view": token_view(tok, base_ids),
            "lora_token_view": token_view(tok, lora_ids),
        }
        results.append(item)

        print(
            f"[{i}] identical={item['token_sequences_identical']} "
            f"base_tokens={len(base_ids)} lora_tokens={len(lora_ids)} "
            f"first_diff={diff}"
        )

    summary = {
        "diagnostic": "Raw token-level Qwen3 base vs FoodInsight V0.3 LoRA comparison",
        "purpose": "Determine whether the observed generation behavior is already present in the base model and whether the LoRA changes generated token sequences.",
        "examples": len(results),
        "identical_sequence_count": sum(r["token_sequences_identical"] for r in results),
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
