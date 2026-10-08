from time import perf_counter
from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.llm.orchestrator import LLMOrchestrator
from app.validation.grounding import GroundingValidator
from app.validation.citations import CitationManager
from app.vision.service import VisionService
from app.vision.query import build_retrieval_query

class ChatService:
    def __init__(
        self,
        rag: RAGPipeline | None = None,
        llm: LLMOrchestrator | None = None,
        vision: VisionService | None = None,
    ):
        self.rag = rag or RAGPipeline()
        self.llm = llm or LLMOrchestrator()
        self.vision = vision or VisionService()
        self.grounding = GroundingValidator()
        self.citations = CitationManager()

    async def answer(
        self,
        message: str,
        document_ids: list[str] | None = None,
        image_path: str | None = None,
    ):
        started = perf_counter()
        vision_result = None
        retrieval_query = message

        if image_path:
            vision_result = await self.vision.analyze(image_path, message)
            retrieval_query = build_retrieval_query(
                message,
                vision_result.observation,
            )

        context, citation_records, retrieved = await self.rag.retrieve_context(
            retrieval_query,
            document_ids or [],
            settings.top_k,
            settings.rerank_top_k,
        )

        # The visual observation is explicitly framed as an observation, not authoritative
        # nutritional/safety data.
        if vision_result:
            observation = vision_result.observation
            visual_context = (
                "\n\nVISUAL OBSERVATION (UNCERTAIN, NOT AUTHORITATIVE):\n"
                f"food candidate: {observation.food_name or 'unknown'}\n"
                f"visible ingredients: {', '.join(observation.visible_ingredients) or 'unknown'}\n"
                f"preparation characteristics: "
                f"{', '.join(observation.preparation_characteristics) or 'unknown'}\n"
                f"observations: {', '.join(observation.visual_observations) or 'none'}\n"
                f"confidence: {observation.confidence}\n"
                f"uncertainty: {', '.join(observation.uncertainty) or 'none'}"
            )
            context = visual_context + "\n\nRETRIEVED EVIDENCE:\n" + context

        response = await self.llm.answer(message, context)
        response, warnings = self.grounding.validate(
            response, citation_records, context
        )
        sources = self.citations.resolve(response.source_refs, citation_records)

        if vision_result:
            warnings.extend(vision_result.observation.warnings)
            if vision_result.observation.uncertainty:
                warnings.append("visual_identification_uncertain")

        return {
            "answer": response.answer,
            "sources": sources,
            "retrieved_chunks": retrieved,
            "confidence": None,
            "warnings": list(dict.fromkeys(warnings)),
            "processing_time_ms": round((perf_counter() - started) * 1000),
            "model": self.llm.provider.model_name,
            "vision": vision_result.model_dump() if vision_result else None,
        }
