from dataclasses import dataclass
from app.rag.models import RetrievedChunk

@dataclass(slots=True)
class CitationRecord:
    title: str
    source: str
    page: int | None
    document_id: str
    chunk_id: str

class ContextBuilder:
    def build(self, chunks: list[RetrievedChunk], max_chars: int = 9000) -> tuple[str, list[CitationRecord]]:
        blocks: list[str] = []
        citations: list[CitationRecord] = []
        used = 0

        for index, item in enumerate(chunks, start=1):
            text = item.chunk.text
            if used + len(text) > max_chars:
                break

            source = str(item.chunk.metadata.get("source") or item.chunk.metadata.get("filename") or "Uploaded document")
            title = str(item.chunk.metadata.get("title") or item.chunk.metadata.get("filename") or source)
            page = item.chunk.page_number

            blocks.append(
                f"[SOURCE {index}]\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Page: {page if page is not None else 'N/A'}\n"
                f"Evidence:\n{text}"
            )
            citations.append(CitationRecord(
                title=title,
                source=source,
                page=page,
                document_id=item.chunk.document_id,
                chunk_id=item.chunk.chunk_id,
            ))
            used += len(text)

        return "\n\n".join(blocks), citations
