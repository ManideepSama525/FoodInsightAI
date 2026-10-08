from __future__ import annotations

from typing import Any
import threading


SYSTEM_INSTRUCTION = (
    "You are FoodInsight-LM, an evidence-aware food intelligence model. "
    "Use only supplied evidence for factual claims. "
    "If evidence is insufficient, say so explicitly. "
    "Preserve numeric values and units. "
    "Do not invent sources, nutrients, portions, or facts."
)


class LocalTransformersProvider:
    """Persistent local Transformers provider using the validated V0.4 raw path.

    The model is loaded lazily once and then retained in memory for subsequent
    requests. The Qwen3 chat template is intentionally not used.
    """

    _instances: dict[str, "LocalTransformersProvider"] = {}
    _instances_lock = threading.Lock()

    def __new__(cls, config):
        key = (
            f"{config.model_id}|"
            f"{config.revision}|"
            f"{config.device}|"
            f"{config.load_in_4bit}|"
            f"{config.load_in_8bit}"
        )

        with cls._instances_lock:
            instance = cls._instances.get(key)

            if instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[key] = instance

        return instance

    def __init__(self, config):
        if getattr(self, "_initialized", False):
            return

        self.config = config
        self._tokenizer = None
        self._model = None
        self._load_lock = threading.Lock()
        self._generation_lock = threading.Lock()
        self._initialized = True

    @property
    def model_name(self) -> str:
        return self.config.model_id

    def _load(self):
        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return

            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
            except ImportError as exc:
                raise RuntimeError(
                    "Local Transformers provider requires torch and transformers. "
                    "Install backend local-model requirements first."
                ) from exc

            kwargs: dict[str, Any] = {}

            if self.config.revision:
                kwargs["revision"] = self.config.revision

            kwargs["trust_remote_code"] = self.config.trust_remote_code

            if self.config.load_in_4bit or self.config.load_in_8bit:
                try:
                    from transformers import BitsAndBytesConfig
                except ImportError as exc:
                    raise RuntimeError(
                        "4-bit/8-bit loading requires a compatible bitsandbytes "
                        "installation."
                    ) from exc

                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=self.config.load_in_4bit,
                    load_in_8bit=self.config.load_in_8bit,
                )
                kwargs["device_map"] = "auto"

            elif self.config.device == "auto":
                kwargs["device_map"] = "auto"

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_id,
                revision=self.config.revision,
                trust_remote_code=self.config.trust_remote_code,
            )

            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.model_id,
                **kwargs,
            )

            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            if self.config.device not in {"auto", "cpu"} and not (
                self.config.load_in_4bit or self.config.load_in_8bit
            ):
                self._model.to(self.config.device)

            self._model.eval()

    def _build_prompt(self, question: str, context: str) -> str:
        user = (
            f"Question:\n{question}\n\n"
            f"Evidence:\n{context}\n\n"
            "Give a concise evidence-grounded answer."
        )

        return (
            f"System:\n{SYSTEM_INSTRUCTION}\n\n"
            f"User:\n{user}\n\n"
            "Assistant:\n"
        )

    async def answer(self, question: str, context: str) -> str:
        self._load()

        import torch

        prompt = self._build_prompt(question, context)

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
        )

        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": self.config.max_new_tokens,
            "do_sample": self.config.temperature > 0,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        if self.config.temperature > 0:
            generation_kwargs["temperature"] = self.config.temperature
            generation_kwargs["top_p"] = self.config.top_p
        else:
            generation_kwargs["temperature"] = None
            generation_kwargs["top_p"] = None
            generation_kwargs["repetition_penalty"] = 1.0

        # Protect the single local model from concurrent generate() calls.
        with self._generation_lock:
            with torch.inference_mode():
                output = self._model.generate(
                    **inputs,
                    **generation_kwargs,
                )

        generated = output[0][inputs["input_ids"].shape[1]:]

        return self._tokenizer.decode(
            generated,
            skip_special_tokens=True,
        ).strip()