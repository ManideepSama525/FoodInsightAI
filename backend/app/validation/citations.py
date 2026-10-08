from app.llm.models import LLMSourceRef
from app.rag.context import CitationRecord

class CitationManager:
    def resolve(
        self,
        refs: list[LLMSourceRef],
        citations: list[CitationRecord],
    ) -> list[dict]:
        output = []
        for ref in refs:
            if 1 <= ref.source_index <= len(citations):
                c = citations[ref.source_index - 1]
                output.append({
                    "title": c.title,
                    "source": c.source,
                    "page": c.page,
                    "document_id": c.document_id,
                    "chunk_id": c.chunk_id,
                })
        return output
