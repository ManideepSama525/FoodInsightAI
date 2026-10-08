from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SYSTEM_INSTRUCTION = (
    "You are FoodInsight-LM, an evidence-aware food intelligence model. "
    "Use only supplied evidence for factual claims. "
    "If evidence is insufficient, say so explicitly. "
    "Preserve numeric values and units. "
    "Do not invent sources, nutrients, portions, or facts."
)


@dataclass(frozen=True)
class FoodInsightPrompt:
    text: str


class FoodInsightRawPromptBuilder:
    """Build the controlled non-chat prompt that avoided the Qwen3 loop."""

    def build(
        self,
        question: str,
        evidence: str = "",
        *,
        extra_instruction: str = "Give a concise evidence-grounded answer.",
    ) -> FoodInsightPrompt:
        user = (
            f"Question:\n{question}\n\n"
            f"Evidence:\n{evidence}\n\n"
            f"{extra_instruction}"
        )
        return FoodInsightPrompt(
            text=(
                f"System:\n{SYSTEM_INSTRUCTION}\n\n"
                f"User:\n{user}\n\n"
                "Assistant:\n"
            )
        )


def build_foodinsight_prompt(
    question: str,
    evidence: str = "",
    *,
    extra_instruction: str = "Give a concise evidence-grounded answer.",
) -> str:
    return FoodInsightRawPromptBuilder().build(
        question,
        evidence,
        extra_instruction=extra_instruction,
    ).text


def generation_kwargs(tokenizer: Any, *, max_new_tokens: int = 128) -> dict[str, Any]:
    """Conservative deterministic settings used by the validated V0.4 raw path."""
    return {
        "max_new_tokens": max_new_tokens,
        "do_sample": False,
        "temperature": None,
        "top_p": None,
        "repetition_penalty": 1.0,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
