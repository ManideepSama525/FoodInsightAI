from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class ParsedPage:
    page_number: int | None
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class TextChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    page_number: int | None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class RetrievedChunk:
    chunk: TextChunk
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
