
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class VerificationAttempt(BaseModel):
    attempt: int
    answer: str
    status: Literal["accepted", "needs_revision", "rejected"]
    unsupported_claim_count: int
    uncertainty: list[str] = []
    changes_requested: list[str] = []


class FeedbackLoopResult(BaseModel):
    final_answer: str
    status: Literal["accepted", "needs_revision", "rejected"]
    attempts: list[VerificationAttempt] = []
    max_attempts_reached: bool = False
    final_uncertainty: list[str] = []
