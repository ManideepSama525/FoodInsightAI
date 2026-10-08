from app.rag.models import TextChunk, RetrievedChunk
from app.rag.reranker import LexicalReranker

def test_reranker_prioritizes_overlap():
    items = [
        RetrievedChunk(TextChunk("1", "d", 0, "apple banana", 1), 0.5),
        RetrievedChunk(TextChunk("2", "d", 1, "unrelated material", 2), 0.5),
    ]
    result = LexicalReranker().rerank("apple", items, 2)
    assert result[0].chunk.chunk_id == "1"
