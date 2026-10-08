from uuid import uuid4
from app.rag.models import ParsedPage, TextChunk

class RecursiveChunker:
    def __init__(self, chunk_size: int = 1200, overlap: int = 180):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, pages: list[ParsedPage], document_id: str) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        index = 0
        for page in pages:
            text = page.text.strip()
            if not text:
                continue
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                segment = text[start:end].strip()
                if segment:
                    chunks.append(
                        TextChunk(
                            chunk_id=str(uuid4()),
                            document_id=document_id,
                            chunk_index=index,
                            text=segment,
                            page_number=page.page_number,
                            metadata=dict(page.metadata),
                        )
                    )
                    index += 1
                if end >= len(text):
                    break
                start = max(0, end - self.overlap)
        return chunks
