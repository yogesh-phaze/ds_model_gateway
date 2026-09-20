import asyncio
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from app.config import settings
from app.metrics import RATE_LIMIT_REJECTIONS_TOTAL


class SlidingWindowRateLimiter:
    """Per-key sliding-window limiter, in-memory and single-process.

    Fine for one gateway instance; state does not survive a restart
    and is not shared across replicas.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.monotonic()

        async with self._lock:
            hits = self._hits[key]

            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()

            if len(hits) >= self.max_requests:
                return False

            hits.append(now)

            return True


rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


async def enforce_rate_limit(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> None:
    key = x_api_key or (
        request.client.host if request.client else "unknown"
    )

    if not await rate_limiter.allow(key):
        RATE_LIMIT_REJECTIONS_TOTAL.inc()

        raise HTTPException(
            status_code=429,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": (
                    f"Rate limit of {settings.RATE_LIMIT_REQUESTS} requests "
                    f"per {settings.RATE_LIMIT_WINDOW_SECONDS:.0f}s exceeded"
                ),
            },
            headers={"Retry-After": str(int(settings.RATE_LIMIT_WINDOW_SECONDS))},
        )
