import time
from collections import defaultdict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > now - self.window]

        if len(self._requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again later.",
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
