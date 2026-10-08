from __future__ import annotations

import re

from app.reasoning.models import UnifiedEvidence
from app.reasoning.numerical import calculate_per_100g
from app.reasoning.numerical_models import NumericalCalculation


class NumericalReasoningService:
    """Deterministic numerical reasoning over retrieved structured evidence."""

    _GRAM_PATTERN = re.compile(
        r"(?P<value>\d+(?:\.\d+)?)\s*g(?:rams?)?\b",
        re.IGNORECASE,
    )

    _NUTRIENTS = (
        "protein",
        "total lipid",
        "fat",
        "carbohydrate",
        "carb",
        "water",
        "fiber",
        "calcium",
        "iron",
        "magnesium",
        "phosphorus",
        "potassium",
        "sodium",
        "zinc",
        "vitamin c",
    )

    @classmethod
    def _extract_portion(cls, query: str) -> float | None:
        match = cls._GRAM_PATTERN.search(query)
        if not match:
            return None
        return float(match.group("value"))

    @classmethod
    def _extract_nutrient(cls, query: str) -> str | None:
        normalized = query.lower()
        for nutrient in sorted(cls._NUTRIENTS, key=len, reverse=True):
            if re.search(r"\b" + re.escape(nutrient) + r"\b", normalized):
                return nutrient
        return None

    @staticmethod
    def _normalize_nutrient_name(name: str) -> str:
        normalized = name.lower().strip()
        normalized = normalized.split(",", 1)[0].strip()
        return normalized

    @classmethod
    def _nutrient_record(
        cls,
        nutrients: dict,
        requested: str,
    ) -> tuple[str, dict] | None:
        requested_normalized = cls._normalize_nutrient_name(requested)

        aliases = {
            "fat": "total lipid",
            "carb": "carbohydrate",
        }
        requested_normalized = aliases.get(
            requested_normalized,
            requested_normalized,
        )

        for name, record in nutrients.items():
            name_normalized = cls._normalize_nutrient_name(str(name))

            if name_normalized == requested_normalized:
                return name, record

        return None

    def calculate(
        self,
        query: str,
        evidence: list[UnifiedEvidence],
    ) -> NumericalCalculation | None:
        portion = self._extract_portion(query)
        nutrient = self._extract_nutrient(query)

        if portion is None or nutrient is None:
            return None

        for item in evidence:
            provenance = item.provenance

            if provenance.get("usda") is not True:
                continue

            nutrients = provenance.get("nutrients") or {}
            match = self._nutrient_record(nutrients, nutrient)

            if match is None:
                continue

            nutrient_name, record = match
            value_per_100g = record.get("value_per_100g")
            unit = record.get("unit")

            if value_per_100g is None or unit is None:
                continue

            calculated = calculate_per_100g(
                value_per_100g=value_per_100g,
                portion_grams=portion,
            )

            food_id = str(provenance.get("food_id", item.source_id))
            food_name = str(provenance.get("food_name", ""))
            source = str(provenance.get("source", ""))

            return NumericalCalculation(
                nutrient=nutrient_name,
                value_per_100g=float(value_per_100g),
                portion_grams=portion,
                calculated_value=calculated,
                unit=str(unit),
                formula=(
                    f"{value_per_100g} {unit}/100 g "
                    f"* {portion:g} g / 100"
                ),
                evidence_id=item.evidence_id,
                food_id=food_id,
                food_name=food_name,
                source=source,
            )

        return None
