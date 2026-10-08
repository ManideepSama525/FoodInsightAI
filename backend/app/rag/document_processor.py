from pathlib import Path
from typing import Protocol
import csv
import json
import re

import fitz

from app.rag.models import ParsedPage

class OCRProvider(Protocol):
    async def extract(self, file_path: str, page_number: int | None = None) -> str:
        ...

class NullOCRProvider:
    async def extract(self, file_path: str, page_number: int | None = None) -> str:
        return ""

class DocumentProcessor:
    """Extracts text while preserving page/source provenance.

    OCR is a fallback: native PDF text is preferred; an OCR provider can be injected
    for scanned pages. Uploaded content remains untrusted data.
    """

    def __init__(self, ocr_provider: OCRProvider | None = None):
        self.ocr_provider = ocr_provider or NullOCRProvider()

    async def process(self, file_path: str, document_id: str) -> list[ParsedPage]:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return await self._pdf(file_path, document_id)
        if suffix == ".txt":
            text = Path(file_path).read_text(encoding="utf-8", errors="replace")
            return [ParsedPage(1, self.clean_text(text), {"format": "txt"})]
        if suffix == ".csv":
            return [ParsedPage(1, self.clean_text(self._csv(file_path)), {"format": "csv"})]
        if suffix == ".json":
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
            return [ParsedPage(1, self.clean_text(json.dumps(data, ensure_ascii=False, indent=2)), {"format": "json"})]
        raise ValueError(f"Unsupported document format: {suffix}")

    async def _pdf(self, file_path: str, document_id: str) -> list[ParsedPage]:
        pages: list[ParsedPage] = []
        with fitz.open(file_path) as pdf:
            for index, page in enumerate(pdf):
                text = self.clean_text(page.get_text("text"))
                metadata = {"format": "pdf", "document_id": document_id}
                if len(text.strip()) < 20:
                    ocr_text = await self.ocr_provider.extract(file_path, index + 1)
                    text = self.clean_text(ocr_text)
                    metadata["ocr_used"] = bool(text)
                pages.append(ParsedPage(index + 1, text, metadata))
        return pages

    @staticmethod
    def _csv(file_path: str) -> str:
        with open(file_path, newline="", encoding="utf-8", errors="replace") as handle:
            rows = csv.reader(handle)
            return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)

    @staticmethod
    def clean_text(text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
