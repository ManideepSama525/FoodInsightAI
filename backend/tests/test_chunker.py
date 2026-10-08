from app.rag.chunker import RecursiveChunker
from app.rag.models import ParsedPage

def test_chunker_preserves_page():
    pages = [ParsedPage(page_number=4, text="A " * 100)]
    chunks = RecursiveChunker(chunk_size=80, overlap=10).chunk(pages, "doc-1")
    assert chunks
    assert all(c.page_number == 4 for c in chunks)
    assert all(c.document_id == "doc-1" for c in chunks)
