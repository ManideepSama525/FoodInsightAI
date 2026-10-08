from __future__ import annotations

import json
from urllib import request as urllib_request


class SemanticVerifierClient:
    """Client for the Windows-side semantic verification service."""

    def __init__(self, url: str = "http://host.docker.internal:8020"):
        self._url = url.rstrip("/")

    async def similarity(
        self,
        claim: str,
        evidence: str,
    ) -> float:
        payload = json.dumps(
            {
                "claim": claim,
                "evidence": evidence,
            }
        ).encode("utf-8")

        req = urllib_request.Request(
            f"{self._url}/similarity",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib_request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        similarity = result.get("similarity")

        if not isinstance(similarity, (int, float)):
            raise RuntimeError(
                "Semantic verifier returned an invalid similarity score."
            )

        return float(similarity)
