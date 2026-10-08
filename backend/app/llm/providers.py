from typing import Protocol
import re

class LLMProvider(Protocol):
    model_name: str

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...

class MockLLMProvider:
    model_name = "mock-grounded-v1"

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Deliberately conservative local provider. It extracts evidence rather than
        # inventing food facts. This is a development fallback, not a benchmark model.
        evidence = re.findall(
            r"\[SOURCE (\d+)\].*?Evidence:\n(.*?)(?=\n\n\[SOURCE|\Z)",
            user_prompt,
            flags=re.S,
        )
        if not evidence:
            return '{"answer":"I could not find sufficient evidence in the available knowledge base.","source_refs":[],"uncertainty":"insufficient_evidence","unsupported_claims":[]}'
        refs = [{"source_index": int(i)} for i, _ in evidence[:3]]
        excerpts = []
        for i, text in evidence[:3]:
            clean = " ".join(text.split())
            excerpts.append(f"[Source {i}] {clean[:700]}")
        answer = "Based on the retrieved evidence:\n\n" + "\n\n".join(excerpts)
        return {
            "answer": answer,
            "source_refs": refs,
            "uncertainty": None,
            "unsupported_claims": [],
        }
