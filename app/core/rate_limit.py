import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            self._buckets[key] = [t for t in self._buckets[key] if now - t < self._window_seconds]
            if len(self._buckets[key]) >= self._max_requests:
                return False
            self._buckets[key].append(now)
            return True


_rate_limiters: dict[str, InMemoryRateLimiter] = {
    "login": InMemoryRateLimiter(max_requests=10, window_seconds=60),
    "signup": InMemoryRateLimiter(max_requests=5, window_seconds=60),
    "chat": InMemoryRateLimiter(max_requests=30, window_seconds=60),
    "order": InMemoryRateLimiter(max_requests=10, window_seconds=60),
    "newsletter": InMemoryRateLimiter(max_requests=5, window_seconds=60),
    "analytics": InMemoryRateLimiter(max_requests=60, window_seconds=60),
    "default": InMemoryRateLimiter(max_requests=120, window_seconds=60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "GET":
            return await call_next(request)

        path = request.url.path
        if "/account/login" in path:
            bucket, prefix = "login", "login"
        elif "/account/signup" in path:
            bucket, prefix = "signup", "signup"
        elif "/api/chat/message" in path:
            bucket, prefix = "chat", "chat"
        elif "/api/orders" in path:
            bucket, prefix = "order", "order"
        elif "/api/analytics/newsletter" in path:
            bucket, prefix = "newsletter", "newsletter"
        elif "/api/analytics" in path:
            bucket, prefix = "analytics", "analytics"
        else:
            bucket, prefix = "default", "default"

        client_ip = request.client.host if request.client else "unknown"
        key = f"{prefix}:{client_ip}"

        limiter = _rate_limiters.get(bucket, _rate_limiters["default"])
        if not limiter.allow(key):
            return Response("Too many requests. Please wait.", status_code=429)

        return await call_next(request)