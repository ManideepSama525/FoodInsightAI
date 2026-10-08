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


def build_messages(example):
    user = (
        f"Question:\n{example['question']}\n\n"
        f"Evidence:\n{example.get('context', '')}\n\n"
        "Give a concise evidence-grounded answer."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]


def make_prompt(tokenizer, example):
    messages = build_messages(example)
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


def inspect_target_template(tokenizer, example):
    messages = build_messages(example)
    full = tokenizer.apply_chat_template(
        messages + [{"role": "assistant", "content": str(example["answer"])}],
        tokenize=False,
        add_generation_prompt=False,
    )
    return full


def generate(model, tokenizer, prompt, mode, max_new_tokens):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    kwargs = dict(
        **inputs,
        do_sample=False,
        max_new_tokens=max_new_tokens,
        pad_token_id=tokenizer.pad_token_id,
        use_cache=True,
    )

    # Test explicit EOS handling without changing the trained model.
    if mode == "eos":
        kwargs["eos_token_id"] = tokenizer.eos_token_id
    elif mode == "im_end":
        im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
        if im_end is not None and im_end != tokenizer.unk_token_id:
            kwargs["eos_token_id"] = im_end
    elif mode == "no_thinking":
        # Qwen3 chat templates can accept this flag. If unsupported by a
        # tokenizer/template, fall back to the normal prompt.
        try:
            messages = build_messages(CURRENT_EXAMPLE)
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            kwargs = dict(
                **inputs,
                do_sample=False,
                max_new_tokens=max_new_tokens,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id,
                use_cache=True,
            )
        except Exception:
            pass

    with torch.inference_mode():
        out = model.generate(**kwargs)

    new_tokens = out[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(new_tokens, skip_special_tokens=False)
    return text


def main():
    global CURRENT_EXAMPLE

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    args = ap.parse_args()

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)

    print("Tokenizer diagnostics:")
    print(" eos_token:", repr(tokenizer.eos_token))
    print(" eos_token_id:", tokenizer.eos_token_id)
    print(" pad_token:", repr(tokenizer.pad_token))
    print(" pad_token_id:", tokenizer.pad_token_id)
    print(" <|im_end|> id:", tokenizer.convert_tokens_to_ids("<|im_end|>"))

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    ds = load_dataset("json", data_files=args.test, split="train")
    n = min(args.limit, len(ds))
    results = []

    modes = ["current", "eos", "im_end", "no_thinking"]

    for i in range(n):
        CURRENT_EXAMPLE = ds[i]
        prompt = make_prompt(tokenizer, CURRENT_EXAMPLE)
        target = inspect_target_template(tokenizer, CURRENT_EXAMPLE)

        row = {
            "index": i,
            "question": CURRENT_EXAMPLE["question"],
            "expected_answer": str(CURRENT_EXAMPLE["answer"]),
            "target_template_ends_with": target[-160:],
            "runs": {},
        }

        for mode in modes:
            print(f"[{i+1}/{n}] {mode}")
            try:
                text = generate(
                    model, tokenizer, prompt, mode, args.max_new_tokens
                )
                row["runs"][mode] = {
                    "text": text,
                    "contains_expected_answer": str(CURRENT_EXAMPLE["answer"]) in text,
                    "contains_im_end": "<|im_end|>" in text,
                    "length_chars": len(text),
                    "for_can_be_converted_count": text.count("ForCanBeConverted"),
                }
            except Exception as exc:
                row["runs"][mode] = {"error": repr(exc)}

        results.append(row)

    payload = {
        "model": "FoodInsight-LM V0.3 QLoRA",
        "base_model": args.base_model,
        "adapter": args.adapter,
        "examples": n,
        "max_new_tokens": args.max_new_tokens,
        "tokenizer": {
            "eos_token": repr(tokenizer.eos_token),
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token": repr(tokenizer.pad_token),
            "pad_token_id": tokenizer.pad_token_id,
            "im_end_id": tokenizer.convert_tokens_to_ids("<|im_end|>"),
        },
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("Saved:", args.output)


if __name__ == "__main__":
    main()
