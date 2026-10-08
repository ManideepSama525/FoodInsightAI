
from __future__ import annotations

import re
from .models import RetrievalPlan


class AdaptiveRetrievalRouter:
    """Deterministic v0 router.

    This is intentionally a research baseline, not the final learned router.
    Later experiments can replace the scoring function with a trained classifier
    without changing the API contract.
    """

    _nutrition = re.compile(
        r"\b(calorie|calories|protein|fat|carb|carbohydrate|fiber|sodium|"
        r"vitamin|minerals?|nutrient|nutrition|serving|100\s*g|mg|kcal)\b",
        re.I,
    )
    _relationship = re.compile(
        r"\b(relationship|related|contains|contain|connected|path|between|"
        r"associated|ingredient.*nutrient|nutrient.*food)\b",
        re.I,
    )
    _research = re.compile(
        r"\b(research|study|studies|paper|literature|evidence|according to|"
        r"published|effect|effects|mechanism)\b",
        re.I,
    )
    _image = re.compile(
        r"\b(image|photo|picture|label|nutrition label|ingredient label|"
        r"what.*shown|analyze.*image)\b",
        re.I,
    )
    _recipe = re.compile(r"\b(recipe|meal|breakfast|lunch|dinner|cook|prepare)\b", re.I)
    _safety = re.compile(
        r"\b(safe|safety|contamin|adulter|allergen|allergy|spoiled|risk|hazard)\b",
        re.I,
    )

    def plan(self, query: str, has_image: bool = False) -> RetrievalPlan:
        q = query.strip()
        weights = {"vector": 0.25, "structured": 0.25, "graph": 0.25, "lexical": 0.25}
        rationale: list[str] = []
        intents: list[str] = []

        if self._nutrition.search(q):
            weights["structured"] += 0.35
            intents.append("nutrition_lookup")
            rationale.append("Nutrition terms favor structured retrieval for exact values.")

        if self._relationship.search(q):
            weights["graph"] += 0.40
            intents.append("relationship_reasoning")
            rationale.append("Relationship language favors knowledge-graph traversal.")

        if self._research.search(q):
            weights["vector"] += 0.40
            intents.append("research_question")
            rationale.append("Research/evidence language favors semantic document retrieval.")

        if self._recipe.search(q):
            weights["structured"] += 0.15
            weights["vector"] += 0.15
            intents.append("recipe_or_meal")

        if self._safety.search(q):
            weights["vector"] += 0.20
            weights["structured"] += 0.15
            intents.append("safety_evidence")

        if has_image or self._image.search(q):
            intents.append("multimodal_analysis")
            rationale.append("Image context requires visual observations plus supporting knowledge retrieval.")

        if not intents:
            intents.append("general_food_question")
            rationale.append("No specialized intent was detected; use balanced hybrid retrieval.")

        total = sum(weights.values())
        weights = {k: round(v / total, 4) for k, v in weights.items()}
        selected = [k for k, v in sorted(weights.items(), key=lambda x: x[1], reverse=True) if v >= 0.20]

        return RetrievalPlan(
            query=q,
            intent="+".join(dict.fromkeys(intents)),
            source_weights=weights,
            selected_sources=selected,
            rationale=rationale,
        )
