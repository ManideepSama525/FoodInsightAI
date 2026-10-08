from app.rag.models import RetrievedChunk

class LexicalReranker:
    """Lightweight deterministic reranker for local operation.

    It combines the original vector score with token overlap. A stronger cross-
    encoder can be injected later without changing the Retriever contract.
    """

    def rerank(self, query: str, chunks: list[RetrievedChunk], limit: int = 5) -> list[RetrievedChunk]:
        query_tokens = {t.lower() for t in query.split() if len(t) > 2}
        scored = []
        for item in chunks:
            text_tokens = {t.lower().strip(".,:;()[]") for t in item.chunk.text.split()}
            overlap = len(query_tokens & text_tokens) / max(len(query_tokens), 1)
            score = 0.75 * item.score + 0.25 * overlap
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        for score, item in scored:
            item.score = score
        return [item for _, item in scored[:limit]]
