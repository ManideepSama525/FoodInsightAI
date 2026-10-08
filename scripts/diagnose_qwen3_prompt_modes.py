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


def build_prompt(tok, ex, mode):
    u = user_text(ex)

    if mode == "chat_current":
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": u},
        ]
        return tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    if mode == "chat_no_think":
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": u},
        ]
        try:
            return tok.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            # Older transformers/template implementations may not expose
            # enable_thinking. Fall back to the documented /no_think suffix.
            return tok.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            ) + " /no_think"

    if mode == "chat_no_think_suffix":
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": u + "\n/no_think"},
        ]
        return tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    if mode == "raw":
        return (
            f"System:\n{SYSTEM}\n\n"
            f"User:\n{u}\n\n"
            "Assistant:\n"
        )

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
    text = tok.decode(ids, skip_special_tokens=False)

    return ids, text


def summarize(tok, ids, text, expected):
    tokens = [tok.convert_ids_to_tokens(x) for x in ids]
    return {
        "token_count": len(ids),
        "tokens_first_50": tokens[:50],
        "text": text,
        "expected_present": bool(expected.strip() and expected.strip() in text),
        "expected_at_start": bool(
            expected.strip() and text.lstrip().startswith(expected.strip())
        ),
        "for_can_be_converted_count": text.count("ForCanBeConverted"),
        "im_end_present": "<|im_end|>" in text,
        "eos_present": "<|endoftext|>" in text,
        "replacement_chars": text.count("�"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    print("Tokenizer chat template:")
    print(tok.chat_template)

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
    modes = [
        "chat_current",
        "chat_no_think",
        "chat_no_think_suffix",
        "raw",
        "direct",
    ]

    results = []

    for i, ex in enumerate(rows):
        item = {
            "index": i,
            "question": ex.get("question", ""),
            "expected_answer": ex.get("answer", ""),
            "modes": {},
        }

        for mode in modes:
            prompt = build_prompt(tok, ex, mode)
            base_ids, base_text = generate(
                base, tok, prompt, args.max_new_tokens
            )
            lora_ids, lora_text = generate(
                lora, tok, prompt, args.max_new_tokens
            )

            item["modes"][mode] = {
                "prompt": prompt,
                "base": summarize(tok, base_ids, base_text, item["expected_answer"]),
                "v03_lora": summarize(tok, lora_ids, lora_text, item["expected_answer"]),
                "base_lora_tokens_identical": base_ids == lora_ids,
            }

            print(
                f"[{i}] {mode}: "
                f"base_loop={item['modes'][mode]['base']['for_can_be_converted_count']} "
                f"lora_loop={item['modes'][mode]['v03_lora']['for_can_be_converted_count']} "
                f"base_im_end={item['modes'][mode]['base']['im_end_present']}"
            )

        results.append(item)

    output = {
        "diagnostic": "Qwen3 prompt-mode generation diagnostic",
        "purpose": "Determine whether the observed looping is caused by chat-template/reasoning prompt construction rather than V0.3 LoRA training.",
        "modes": modes,
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
