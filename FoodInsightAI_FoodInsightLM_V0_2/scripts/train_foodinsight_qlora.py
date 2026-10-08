from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)

ROOT = Path(__file__).resolve().parents[1]

# V0.3 is the validated training baseline.
DATASET_DIR = ROOT / "research" / "dataset" / "foodinsight_lm" / "v0_3"
TRAIN_FILE = DATASET_DIR / "foodinsight_usda_v0_3_train.jsonl"
VAL_FILE = DATASET_DIR / "foodinsight_usda_v0_3_validation.jsonl"
META_FILE = DATASET_DIR / "foodinsight_usda_v0_3_metadata.json"

# Local model if present; otherwise Transformers can download the public model.
DEFAULT_LOCAL_MODEL = ROOT / "models" / "Qwen3-1.7B-Base"
MODEL = os.getenv(
    "BASE_MODEL",
    str(DEFAULT_LOCAL_MODEL) if DEFAULT_LOCAL_MODEL.exists() else "Qwen/Qwen3-1.7B-Base",
)

OUT = ROOT / "artifacts" / "foodinsight_qwen3_1.7b_v03_qlora"

MAX_LEN = int(os.getenv("MAX_SEQ_LENGTH", "768"))
EPOCHS = float(os.getenv("NUM_EPOCHS", "2"))
BATCH = int(os.getenv("TRAIN_BATCH_SIZE", "1"))
ACC = int(os.getenv("GRADIENT_ACCUMULATION_STEPS", "16"))
LR = float(os.getenv("LEARNING_RATE", "0.00015"))
SEED = int(os.getenv("SEED", "20261001"))


def seed_all(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_prompt(tokenizer, example: dict) -> tuple[str, str]:
    system = (
        "You are FoodInsight-LM, an evidence-aware food intelligence model. "
        "Use only supplied evidence for factual claims. "
        "If evidence is insufficient, say so explicitly. "
        "Preserve numeric values and units. "
        "Do not invent sources, nutrients, portions, or facts."
    )

    user = (
        f"Question:\n{example['question']}\n\n"
        f"Evidence:\n{example.get('context', '')}\n\n"
        "Give a concise evidence-grounded answer."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    if tokenizer.chat_template:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        full = tokenizer.apply_chat_template(
            messages + [{"role": "assistant", "content": str(example["answer"])}],
            tokenize=False,
            add_generation_prompt=False,
        )
    else:
        prompt = f"System:\n{system}\n\nUser:\n{user}\n\nAssistant:\n"
        full = prompt + str(example["answer"])

    return prompt, full


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this QLoRA training run.")

    seed_all(SEED)

    for path in (TRAIN_FILE, VAL_FILE, META_FILE):
        if not path.exists():
            raise SystemExit(f"Missing V0.3 dataset artifact: {path}")

    metadata = json.loads(META_FILE.read_text(encoding="utf-8"))

    if metadata.get("dataset_version") != "v0.3":
        raise SystemExit("Dataset metadata is not v0.3.")

    if metadata.get("train_tasks") != 46005:
        raise SystemExit(
            f"Unexpected V0.3 train count: {metadata.get('train_tasks')}"
        )

    if metadata.get("validation_tasks") != 5757:
        raise SystemExit(
            f"Unexpected V0.3 validation count: {metadata.get('validation_tasks')}"
        )

    print("=" * 78)
    print("FOODINSIGHT-LM V0.3 QLoRA SFT")
    print("=" * 78)
    print(f"Base model: {MODEL}")
    print(f"Train:      {TRAIN_FILE}")
    print(f"Validation: {VAL_FILE}")
    print(f"Output:     {OUT}")
    print(f"GPU:        {torch.cuda.get_device_name(0)}")
    print(f"VRAM GiB:   {torch.cuda.get_device_properties(0).total_memory / 2**30:.2f}")
    print(f"BF16:       {torch.cuda.is_bf16_supported()}")
    print()

    if not DEFAULT_LOCAL_MODEL.exists() and MODEL == "Qwen/Qwen3-1.7B-Base":
        print("Local Qwen3-1.7B-Base not found.")
        print("Transformers will download the public base model from Hugging Face.")
        print()

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    compute_dtype = (
        torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    )

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )

    print("Loading base model in 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
    )

    model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    lora = LoraConfig(
        r=32,
        lora_alpha=64,
        lora_dropout=0.05,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        task_type="CAUSAL_LM",
        bias="none",
    )

    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    print()
    print("Loading V0.3 train/validation JSONL...")
    ds = load_dataset(
        "json",
        data_files={
            "train": str(TRAIN_FILE),
            "validation": str(VAL_FILE),
        },
    )

    def encode(example: dict) -> dict:
        prompt, full = build_prompt(tokenizer, example)

        prompt_tokens = tokenizer(
            prompt,
            add_special_tokens=False,
        )

        full_tokens = tokenizer(
            full,
            add_special_tokens=False,
            truncation=True,
            max_length=MAX_LEN,
        )

        input_ids = full_tokens["input_ids"]
        attention_mask = full_tokens["attention_mask"]

        labels = input_ids.copy()

        prompt_len = min(len(prompt_tokens["input_ids"]), len(labels))
        labels[:prompt_len] = [-100] * prompt_len

        # Keep only examples with at least one supervised answer token.
        if not any(x != -100 for x in labels):
            labels[-1] = input_ids[-1]

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    cols = ds["train"].column_names
    encoded = ds.map(
        encode,
        remove_columns=cols,
        desc="Tokenizing V0.3",
    )

    OUT.mkdir(parents=True, exist_ok=True)

    bf16 = torch.cuda.is_bf16_supported()

    args = TrainingArguments(
        output_dir=str(OUT),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=ACC,
        learning_rate=LR,
        warmup_steps=0.05,
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        bf16=bf16,
        fp16=not bf16,
        gradient_checkpointing=True,
        optim="adamw_torch",
        report_to="none",
        seed=SEED,
        remove_unused_columns=False,
    )

    collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        label_pad_token_id=-100,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=encoded["train"],
        eval_dataset=encoded["validation"],
        data_collator=collator,
    )

    print()
    print("=" * 78)
    print("TRAINING START")
    print("=" * 78)
    print("V0.3 test set is NOT loaded and will NOT be used during training.")
    print()

    start = time.perf_counter()
    result = trainer.train()
    elapsed = time.perf_counter() - start

    trainer.save_model(str(OUT))
    tokenizer.save_pretrained(str(OUT))

    metrics = dict(result.metrics)
    metrics["wall_clock_seconds"] = round(elapsed, 3)

    meta = {
        "base_model": MODEL,
        "training": "4bit QLoRA SFT",
        "dataset": "foodinsight_usda_v0_3",
        "dataset_version": "v0.3",
        "train_tasks": metadata["train_tasks"],
        "validation_tasks": metadata["validation_tasks"],
        "test_tasks": metadata["test_tasks"],
        "test_used_during_training": False,
        "epochs": EPOCHS,
        "max_seq_length": MAX_LEN,
        "batch": BATCH,
        "gradient_accumulation": ACC,
        "learning_rate": LR,
        "seed": SEED,
        "gpu": torch.cuda.get_device_name(0),
        "gpu_vram_gib": round(
            torch.cuda.get_device_properties(0).total_memory / 2**30, 3
        ),
        "bf16": bf16,
        "target_modules": list(lora.target_modules),
        "train_metrics": metrics,
    }

    (OUT / "training_metadata.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )

    print()
    print(json.dumps(meta, indent=2))
    print()
    print("=" * 78)
    print("FOODINSIGHT-LM V0.3 QLORA TRAINING: COMPLETE")
    print("=" * 78)


if __name__ == "__main__":
    main()
