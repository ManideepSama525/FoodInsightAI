from collections import defaultdict, deque
from time import monotonic
from threading import Lock

class InMemoryRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit=limit
        self.window=window_seconds
        self.events=defaultdict(deque)
        self.lock=Lock()

    def allow(self, key: str) -> bool:
        now=monotonic()
        with self.lock:
            q=self.events[key]
            while q and now-q[0] >= self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True
