import asyncio
from pathlib import Path
from app.rag.document_processor import DocumentProcessor

def test_text_processing(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("Food safety\n\nTemperature control.", encoding="utf-8")
    pages = asyncio.run(DocumentProcessor().process(str(path), "doc-1"))
    assert len(pages) == 1
    assert "Temperature control" in pages[0].text
