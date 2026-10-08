from typing import Protocol
import hashlib
import math

class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int:
        ...

    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

class DeterministicEmbeddingProvider:
    """Offline development embedding.

    It is deterministic and dependency-free, but is NOT intended as a semantic
    benchmark embedding model. Production deployments should configure a real
    pretrained embedding provider.
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self._dimension
            tokens = text.lower().split()
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % self._dimension
                sign = 1.0 if digest[4] % 2 else -1.0
                vector[idx] += sign
            norm = math.sqrt(sum(x * x for x in vector)) or 1.0
            vectors.append([x / norm for x in vector])
        return vectors
