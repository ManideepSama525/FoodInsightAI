from __future__ import annotations

import json
from urllib import request as urllib_request

from app.core.config import settings
from app.llm.providers import MockLLMProvider, LLMProvider


class LocalLLMProviderAdapter:
    model_name = "foodinsight-local"

    def __init__(self):
        self._url = "http://host.docker.internal:8010/generate"

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "question": user_prompt,
            "context": system_prompt,
            "max_new_tokens": 512,
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib_request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RuntimeError(
                f"Local model server request failed: {exc}"
            ) from exc

        answer = result.get("answer")

        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "Local model server returned an invalid or empty answer."
            )

        return json.dumps(
            {
                "answer": answer.strip(),
                "source_refs": [],
                "uncertainty": None,
                "unsupported_claims": [],
            }
        )


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLMProvider()

    if settings.llm_provider == "local":
        return LocalLLMProviderAdapter()

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER={settings.llm_provider!r}. "
        "Supported providers: mock, local."
    )

