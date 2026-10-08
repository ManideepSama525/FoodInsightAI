import json
from app.llm.models import LLMResponse
from app.llm.prompts import build_grounded_prompt
from app.llm.provider_factory import get_llm_provider

class LLMOrchestrator:
    def __init__(self, provider=None):
        self.provider = provider or get_llm_provider()

    async def answer(self, query: str, context: str) -> LLMResponse:
        system, user = build_grounded_prompt(query, context)
        raw = await self.provider.generate(system, user)

        if isinstance(raw, dict):
            return LLMResponse.model_validate(raw)

        try:
            parsed = json.loads(raw)
            return LLMResponse.model_validate(parsed)
        except Exception:
            # Provider output is untrusted. Do not pass malformed output through.
            return LLMResponse(
                answer="I could not produce a validated grounded response.",
                source_refs=[],
                uncertainty="malformed_model_output",
                unsupported_claims=[],
            )
