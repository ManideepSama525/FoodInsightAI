import argparse
import json
from pathlib import Path
from collections import Counter

from datasets import load_dataset
from transformers import AutoTokenizer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--train", required=True)
    ap.add_argument("--validation", required=False)
    ap.add_argument("--test", required=False)
    ap.add_argument("--output", required=True)
    ap.add_argument("--scan-limit", type=int, default=0)
    args = ap.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)

    report = {
        "tokenizer": {
            "eos_token": tokenizer.eos_token,
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token": tokenizer.pad_token,
            "pad_token_id": tokenizer.pad_token_id,
            "im_end_token_id": tokenizer.convert_tokens_to_ids("<|im_end|>"),
            "for_can_be_converted_token_ids": tokenizer.encode(
                "ForCanBeConverted", add_special_tokens=False
            ),
        },
        "datasets": {}
    }

    def scan(path, name):
        ds = load_dataset("json", data_files=path, split="train")
        limit = len(ds) if args.scan_limit == 0 else min(args.scan_limit, len(ds))

        hits = []
        answer_counter = Counter()
        context_counter = Counter()
        question_counter = Counter()

        for i in range(limit):
            ex = ds[i]
            raw = json.dumps(ex, ensure_ascii=False)
            answer = str(ex.get("answer", ""))
            context = str(ex.get("context", ""))
            question = str(ex.get("question", ""))

            if "ForCanBeConverted" in raw:
                hits.append({
                    "index": i,
                    "question": question,
                    "answer": answer,
                    "context_contains": "ForCanBeConverted" in context,
                    "answer_contains": "ForCanBeConverted" in answer,
                    "raw_excerpt": raw[:3000],
                })

            if answer:
                answer_counter[answer] += 1
            if "ForCanBeConverted" in context:
                context_counter["context"] += 1
            if "ForCanBeConverted" in answer:
                context_counter["answer"] += 1

            question_counter["examples"] += 1

        report["datasets"][name] = {
            "path": path,
            "examples": len(ds),
            "scanned": limit,
            "for_can_be_converted_hits": len(hits),
            "for_can_be_converted_examples": hits[:50],
            "for_can_be_converted_in_context": context_counter["context"],
            "for_can_be_converted_in_answer": context_counter["answer"],
            "unique_answers": len(answer_counter),
        }

    scan(args.train, "train")
    if args.validation:
        scan(args.validation, "validation")
    if args.test:
        scan(args.test, "test")

    # Token-level diagnostic: inspect the exact target shape for a few examples.
    ds = load_dataset("json", data_files=args.train, split="train")
    target_samples = []
    for i in range(min(5, len(ds))):
        ex = ds[i]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are FoodInsight-LM, an evidence-aware food intelligence model. "
                    "Use only supplied evidence for factual claims. "
                    "If evidence is insufficient, say so explicitly. "
                    "Preserve numeric values and units. "
                    "Do not invent sources, nutrients, portions, or facts."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{ex['question']}\n\n"
                    f"Evidence:\n{ex.get('context', '')}\n\n"
                    "Give a concise evidence-grounded answer."
                ),
            },
        ]
        full = tokenizer.apply_chat_template(
            messages + [{"role": "assistant", "content": str(ex["answer"])}],
            tokenize=False,
            add_generation_prompt=False,
        )
        ids = tokenizer(full, add_special_tokens=False)["input_ids"]
        decoded_tail = tokenizer.decode(ids[-80:], skip_special_tokens=False)
        target_samples.append({
            "index": i,
            "answer": str(ex["answer"]),
            "contains_for_can_be_converted": "ForCanBeConverted" in full,
            "contains_im_end": "<|im_end|>" in full,
            "tail": decoded_tail,
            "last_20_token_ids": ids[-20:],
        })

    report["target_samples"] = target_samples

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Saved:", args.output)
    print(json.dumps(report["tokenizer"], indent=2, ensure_ascii=False))
    for name, d in report["datasets"].items():
        print(
            f"{name}: {d['examples']} examples; "
            f"scanned={d['scanned']}; "
            f"ForCanBeConverted hits={d['for_can_be_converted_hits']}; "
            f"context={d['for_can_be_converted_in_context']}; "
            f"answer={d['for_can_be_converted_in_answer']}"
        )


if __name__ == "__main__":
    main()
