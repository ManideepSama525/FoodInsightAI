import asyncio
from app.rag.embeddings import DeterministicEmbeddingProvider

def test_embeddings_are_deterministic():
    provider = DeterministicEmbeddingProvider(64)
    a = asyncio.run(provider.embed(["spinach nutrition"]))
    b = asyncio.run(provider.embed(["spinach nutrition"]))
    assert a == b
    assert len(a[0]) == 64
