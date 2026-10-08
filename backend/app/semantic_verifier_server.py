from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import torch


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

device = "cuda" if torch.cuda.is_available() else "cpu"

model = SentenceTransformer(
    MODEL_ID,
    device=device,
)


class SimilarityRequest(BaseModel):
    claim: str
    evidence: str


class SimilarityResponse(BaseModel):
    similarity: float
    model: str
    device: str


app = FastAPI(
    title="FoodInsightAI Semantic Verifier",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "foodinsightai-semantic-verifier",
        "model": MODEL_ID,
        "device": device,
    }


@app.post("/similarity", response_model=SimilarityResponse)
async def similarity(request: SimilarityRequest):
    embeddings = model.encode(
        [request.claim, request.evidence],
        normalize_embeddings=True,
    )

    score = float(embeddings[0] @ embeddings[1])

    return SimilarityResponse(
        similarity=round(score, 6),
        model=MODEL_ID,
        device=device,
    )
