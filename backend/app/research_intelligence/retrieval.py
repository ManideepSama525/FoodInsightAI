from __future__ import annotations

import re
from dataclasses import dataclass

from app.rag.pipeline import RAGPipeline
from app.nutrition.service import NutritionService
from app.knowledge.bootstrap import bootstrap_demo_graph_neo4j
from app.reasoning.models import RetrievalSignal
from .models import RetrievalPlan
from .router import AdaptiveRetrievalRouter
from .usda import USDAEvidenceService


@dataclass
class ResearchRetrievalResult:
    plan: RetrievalPlan
    vector: list[RetrievalSignal]
    lexical: list[RetrievalSignal]
    structured: list[RetrievalSignal]
    graph: list[RetrievalSignal]
    warnings: list[str]


class ResearchRetrievalService:
    """Connects the research router to the existing retrieval engines.

    The service intentionally preserves the existing RAG/nutrition/graph
    interfaces. It is an integration layer, not a replacement database.
    """

    def __init__(
        self,
        rag: RAGPipeline | None = None,
        nutrition: NutritionService | None = None,
        usda: USDAEvidenceService | None = None,
    ):
        self.router = AdaptiveRetrievalRouter()
        self.rag = rag or RAGPipeline()
        self.nutrition = nutrition or NutritionService()
        self.usda = usda or USDAEvidenceService()
        self.graph = bootstrap_demo_graph_neo4j()

    @staticmethod
    def _is_evidence_request(query: str) -> bool:
        normalized = query.lower().strip()

        evidence_phrases = (
            "what evidence supports",
            "what evidence support",
            "what is the evidence for",
            "show the evidence",
            "show me the evidence",
            "which evidence supports",
            "what source supports",
            "which source supports",
            "what sources support",
        )

        return any(
            phrase in normalized
            for phrase in evidence_phrases
        )

    async def retrieve(
        self,
        query: str,
        has_image: bool = False,
        document_ids: list[str] | None = None,
        top_k: int = 8,
    ) -> ResearchRetrievalResult:
        plan = self.router.plan(
            query,
            has_image=has_image,
        )
        warnings: list[str] = []

        vector: list[RetrievalSignal] = []
        lexical: list[RetrievalSignal] = []
        structured: list[RetrievalSignal] = []
        graph: list[RetrievalSignal] = []

        selected = set(plan.selected_sources)

        # Evidence-trace requests must have access to structured evidence.
        # This ensures USDA evidence is searched even when the adaptive
        # router initially selects only vector retrieval.
        if self._is_evidence_request(query):
            selected.add("structured")

        # Vector + lexical signals come from the existing RAG pipeline.
        # If the vector store is unavailable, the rest of the research
        # pipeline still returns structured/graph evidence rather than
        # failing entirely.
        if "vector" in selected or "lexical" in selected:
            try:
                _, _, chunks = await self.rag.retrieve_context(
                    query=query,
                    document_ids=document_ids,
                    top_k=top_k,
                    rerank_top_k=top_k,
                )

                for idx, item in enumerate(chunks):
                    signal = RetrievalSignal(
                        source_type=(
                            "vector"
                            if "vector" in selected
                            else "lexical"
                        ),
                        source_id=str(item["chunk_id"]),
                        score=max(
                            0.0,
                            float(item["score"]),
                        ),
                        content=str(item["text"]),
                        metadata={
                            "document_id": item["document_id"],
                            "page": item["page"],
                            "rank": idx + 1,
                        },
                    )

                    if "vector" in selected:
                        vector.append(signal)

                    if "lexical" in selected:
                        lexical.append(signal)

            except Exception as exc:
                warnings.append(
                    "Document/vector retrieval unavailable: "
                    f"{type(exc).__name__}."
                )

        # Structured nutrition retrieval.
        if "structured" in selected:
            matches = self.nutrition.search(query)

            if not matches:
                # A light token fallback helps questions such as
                # "protein in lentils" resolve to "lentils".
                for token in re.findall(
                    r"[A-Za-z]{3,}",
                    query.lower(),
                ):
                    matches.extend(
                        self.nutrition.search(token)
                    )

                unique = {
                    m["food_id"]: m
                    for m in matches
                }
                matches = list(unique.values())

            for rank, record in enumerate(
                matches[:top_k],
                start=1,
            ):
                nutrients = record["nutrients"]

                content = (
                    f"{record['name']}: "
                    f"{nutrients['calories_kcal']} kcal, "
                    f"{nutrients['protein_g']} g protein, "
                    f"{nutrients['carbohydrates_g']} g carbohydrates, "
                    f"{nutrients['fat_g']} g fat, "
                    f"{nutrients['fiber_g']} g fiber, "
                    f"{nutrients['sodium_mg']} mg sodium "
                    f"per {record['serving_g']} g. "
                    f"Source: {record['source']}."
                )

                structured.append(
                    RetrievalSignal(
                        source_type="structured",
                        source_id=str(record["food_id"]),
                        score=1.0 / rank,
                        content=content,
                        metadata={
                            "food_id": record["food_id"],
                            "food_name": record["name"],
                            "serving_g": record["serving_g"],
                            "synthetic": record["synthetic"],
                            "source": record["source"],
                        },
                    )
                )

        # USDA structured evidence retrieval.
        if "structured" in selected:
            try:
                usda_matches = self.usda.search(
                    query,
                    top_k=top_k,
                )

                seen_usda_ids = {
                    item.source_id
                    for item in structured
                    if item.metadata.get("usda") is True
                }

                for match in usda_matches:
                    food_id = str(match["food_id"])

                    if food_id in seen_usda_ids:
                        continue

                    seen_usda_ids.add(food_id)

                    structured.append(
                        RetrievalSignal(
                            source_type="structured",
                            source_id=food_id,
                            score=max(
                                0.0,
                                float(
                                    match.get(
                                        "_retrieval_score",
                                        0.0,
                                    )
                                ),
                            ),
                            content=str(
                                match["context"]
                            ),
                            metadata={
                                "food_id": match["food_id"],
                                "food_name": match["food_name"],
                                "category": match["category"],
                                "source": match["source"],
                                "synthetic": False,
                                "usda": True,
                                "nutrients": match["nutrients"],
                                "portions": match["portions"],
                            },
                        )
                    )

            except Exception as exc:
                warnings.append(
                    "USDA structured retrieval unavailable: "
                    f"{type(exc).__name__}."
                )

        # Knowledge graph retrieval.
        if "graph" in selected:
            q = query.lower()
            entities = []

            for entity in self.graph.entities.values():
                terms = [
                    entity.canonical_name,
                    *entity.aliases,
                ]

                if any(
                    term.lower() in q
                    for term in terms
                ):
                    entities.append(entity)

            for entity in entities[:top_k]:
                neighbors = self.graph.neighbors(
                    entity.entity_id
                )

                for relation in neighbors[:top_k]:
                    subject = self.graph.get_entity(
                        relation.subject_id
                    )
                    obj = self.graph.get_entity(
                        relation.object_id
                    )

                    if not subject or not obj:
                        continue

                    content = (
                        f"{subject.canonical_name} "
                        f"--{relation.predicate}--> "
                        f"{obj.canonical_name} "
                        f"(confidence "
                        f"{relation.confidence:.2f})."
                    )

                    graph.append(
                        RetrievalSignal(
                            source_type="graph",
                            source_id=relation.relation_id,
                            score=float(
                                relation.confidence
                            ),
                            content=content,
                            metadata={
                                "subject_id": relation.subject_id,
                                "predicate": relation.predicate,
                                "object_id": relation.object_id,
                                "source_ids": relation.source_ids,
                            },
                        )
                    )

        return ResearchRetrievalResult(
            plan=plan,
            vector=vector,
            lexical=lexical,
            structured=structured,
            graph=graph,
            warnings=warnings,
        )