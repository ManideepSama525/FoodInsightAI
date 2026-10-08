import asyncio
from app.security.rate_limit import InMemoryRateLimiter

def test_rate_limiter():
    limiter=InMemoryRateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("test")
    assert limiter.allow("test")
    assert not limiter.allow("test")

def test_live_probe():
    from app.api.v1.routes.system import live
    assert asyncio.run(live())["status"]=="ok"
