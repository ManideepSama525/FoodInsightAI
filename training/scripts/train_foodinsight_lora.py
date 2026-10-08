from __future__ import annotations

import json
import os
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = Path(os.getenv("MODEL_DIR", "models/SmolLM2-360M-Instruct"))
DATA_DIR = ROOT / "research/dataset/foodinsight_lm/training_ready"
OUTPUT_DIR = Path(os.getenv("TRAIN_OUTPUT_DIR", "artifacts/foodinsight_lora"))

MAX_LENGTH = int(os.getenv("MAX_SEQ_LENGTH", "512"))
EPOCHS = float(os.getenv("NUM_EPOCHS", "2"))
BATCH = int(os.getenv("TRAIN_BATCH_SIZE", "1"))
EVAL_BATCH = int(os.getenv("EVAL_BATCH_SIZE", "1"))
GRAD_ACCUM = int(os.getenv("GRADIENT_ACCUMULATION_STEPS", "8"))
LR = float(os.getenv("LEARNING_RATE", "0.0002"))
WARMUP = float(os.getenv("WARMUP_RATIO", "0.03"))
LORA_R = int(os.getenv("LORA_R", "16"))
LORA_ALPHA = int(os.getenv("LORA_ALPHA", "32"))
LORA_DROPOUT = float(os.getenv("LORA_DROPOUT", "0.05"))
SEED = int(os.getenv("SEED", "20261001"))


def format_record(example, tokenizer):
    question = str(example.get("question", "")).strip()
    context = str(example.get("context", "")).strip()
    answer = str(example.get("answer", "")).strip()

    if not question or not answer:
        return {"text": ""}

    user = f"Question:\n{question}\n\nEvidence:\n{context or 'No additional evidence provided.'}\n\nAnswer only from the evidence."

    messages = [
        {
            "role": "system",
            "content": (
                "You are FoodInsightAI, an evidence-aware food intelligence "
                "assistant. Give concise, grounded answers. Do not invent facts."
            ),
        },
        {"role": "user", "content": user},
        {"role": "assistant", "content": answer},
    ]

    if tokenizer.chat_template:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
    else:
        text = (
            "System:\n"
            + messages[0]["content"]
            + "\n\nUser:\n"
            + user
            + "\n\nAssistant:\n"
            + answer
        )

    return {"text": text}


def detect_lora_targets(model):
    preferred = {"q_proj", "k_proj", "v_proj", "o_proj"}
    found = set()

    for name, _module in model.named_modules():
        leaf = name.rsplit(".", 1)[-1]
        if leaf in preferred:
            found.add(leaf)

    if not found:
        raise RuntimeError(
            "Could not find standard attention projection modules for LoRA."
        )

    return sorted(found)


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the default training path.")

    model_path = ROOT / MODEL_DIR
    if not model_path.exists():
        raise SystemExit(
            f"Model not found at {model_path}. Run download_baseline.cmd first."
        )

    train_path = DATA_DIR / "train.jsonl"
    val_path = DATA_DIR / "validation.jsonl"
    if not train_path.exists() or not val_path.exists():
        raise SystemExit(
            "Training dataset not prepared. Run prepare_dataset.cmd first."
        )

    print("GPU:", torch.cuda.get_device_name(0))
    print("Model:", model_path)
    print("Output:", ROOT / OUTPUT_DIR)

    tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        torch_dtype=dtype,
    )

    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    targets = detect_lora_targets(model)
    print("LoRA target modules:", targets)

    lora = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=targets,
        task_type="CAUSAL_LM",
        bias="none",
    )

    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(train_path),
            "validation": str(val_path),
        },
    )

    dataset = dataset.map(
        lambda ex: format_record(ex, tokenizer),
        remove_columns=dataset["train"].column_names,
    )

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=MAX_LENGTH,
        )

    tokenized = dataset.map(
        tokenize,
        batched=True,
        remove_columns=["text"],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(
        output_dir=str(ROOT / OUTPUT_DIR),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH,
        per_device_eval_batch_size=EVAL_BATCH,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        warmup_ratio=WARMUP,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        fp16=True,
        gradient_checkpointing=True,
        report_to="none",
        seed=SEED,
        remove_unused_columns=False,
    )

    collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=collator,
    )

    trainer.train()
    trainer.save_model(str(ROOT / OUTPUT_DIR))
    tokenizer.save_pretrained(str(ROOT / OUTPUT_DIR))

    metadata = {
        "base_model": str(model_path),
        "training_mode": "lora",
        "max_seq_length": MAX_LENGTH,
        "epochs": EPOCHS,
        "train_batch_size": BATCH,
        "gradient_accumulation_steps": GRAD_ACCUM,
        "learning_rate": LR,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "seed": SEED,
        "gpu": torch.cuda.get_device_name(0),
    }
    (ROOT / OUTPUT_DIR / "training_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("TRAINING COMPLETE")
    print("Adapter:", ROOT / OUTPUT_DIR)


if __name__ == "__main__":
    main()
