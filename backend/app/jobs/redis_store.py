from __future__ import annotations
import json
from typing import Any

class RedisJobStore:
    """Optional Redis coordination layer; import is lazy for local development."""
    def __init__(self, url: str):
        self.url = url
        self._client = None

    async def connect(self):
        if self._client is None:
            from redis.asyncio import Redis
            self._client = Redis.from_url(self.url, decode_responses=True)
            await self._client.ping()
        return self

    async def publish(self, channel: str, payload: dict[str, Any]):
        await self._client.publish(channel, json.dumps(payload, default=str))

    async def set_job(self, job_id: str, payload: dict[str, Any], ttl: int = 86400):
        await self._client.set(f"foodinsight:job:{job_id}", json.dumps(payload, default=str), ex=ttl)

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        raw = await self._client.get(f"foodinsight:job:{job_id}")
        return json.loads(raw) if raw else None
