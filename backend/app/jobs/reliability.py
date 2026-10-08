from dataclasses import dataclass
import asyncio
import random

@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    jitter: float = 0.15

    def delay(self, attempt: int) -> float:
        raw = min(self.max_delay_seconds, self.base_delay_seconds * (2 ** max(0, attempt - 1)))
        return raw * (1 + random.uniform(-self.jitter, self.jitter))

async def backoff(policy: RetryPolicy, attempt: int):
    await asyncio.sleep(policy.delay(attempt))
