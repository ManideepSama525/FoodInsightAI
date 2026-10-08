from __future__ import annotations

import json
import re
from pathlib import Path


class USDAEvidenceService:
    """Read-only search over the extracted USDA FNDDS evidence index."""

    def __init__(
        self,
        path: str | Path = Path("data") / "usda" / "usda_evidence_v03.jsonl",
    ):
        self.path = Path(path)
        self._records: list[dict] | None = None

    def _load(self) -> list[dict]:
        if self._records is None:
            with self.path.open("r", encoding="utf-8") as f:
                self._records = [
                    json.loads(line)
                    for line in f
                    if line.strip()
                ]
        return self._records

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) >= 3
        }

    @staticmethod
    def _normalized(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())

    def _score(self, query: str, record: dict) -> float:
        normalized_query = self._normalized(query)
        food_name = self._normalized(record.get("food_name", ""))

        query_tokens = self._tokens(query)
        food_tokens = self._tokens(food_name)
        category_tokens = self._tokens(record.get("category", ""))

        score = 0.0

        # Exact food-name phrase is the strongest signal.
        if food_name and food_name in normalized_query:
            score += 100.0

        # Food-name token overlap.
        score += len(query_tokens & food_tokens) * 5.0

        # Category overlap is weaker.
        score += len(query_tokens & category_tokens) * 1.0

        # Nutrient-name overlap.
        for nutrient_name in record.get("nutrients", {}):
            if query_tokens & self._tokens(nutrient_name):
                score += 2.0

        # Handle explicit "no X" constraints.
        no_terms = re.findall(
            r"\bno\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)",
            normalized_query,
        )

        for phrase in no_terms:
            phrase_tokens = self._tokens(phrase)

            if phrase_tokens and phrase_tokens.issubset(food_tokens):
                score += 15.0

            # A record explicitly containing "with X" conflicts
            # with a query containing "no X".
            if re.search(
                r"\bwith\s+" + re.escape(phrase) + r"\b",
                food_name,
            ):
                score -= 25.0

        # Handle explicit "with X" constraints.
        with_terms = re.findall(
            r"\bwith\s+([a-z0-9]+(?:\s+[a-z0-9]+)*)",
            normalized_query,
        )

        for phrase in with_terms:
            if re.search(
                r"\bwith\s+" + re.escape(phrase) + r"\b",
                food_name,
            ):
                score += 15.0

            if re.search(
                r"\bno\s+" + re.escape(phrase) + r"\b",
                food_name,
            ):
                score -= 25.0

        return score

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        records = self._load()

        if not self._tokens(query):
            return []

        scored: list[tuple[float, dict]] = []

        for record in records:
            score = self._score(query, record)

            if score > 0:
                scored.append((score, record))

        scored.sort(
            key=lambda item: (
                item[0],
                item[1].get("food_name", ""),
            ),
            reverse=True,
        )

        return [
            {
                **record,
                "_retrieval_score": score,
            }
            for score, record in scored[:top_k]
        ]

