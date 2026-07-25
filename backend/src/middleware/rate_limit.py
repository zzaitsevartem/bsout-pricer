import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

SWEEP_EVERY = 1000


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_requests: int = 60,
        window: int = 60,
        trust_forwarded_for: bool = False,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.trust_forwarded_for = trust_forwarded_for
        self._requests: dict[str, list[float]] = {}
        self._since_sweep = 0

    def _client_key(self, request: Request) -> str:
        if self.trust_forwarded_for:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _sweep(self, now: float) -> None:
        cutoff = now - self.window
        for key in [k for k, v in self._requests.items() if not v or v[-1] <= cutoff]:
            del self._requests[key]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        client_ip = self._client_key(request)
        now = time.time()

        self._since_sweep += 1
        if self._since_sweep >= SWEEP_EVERY:
            self._since_sweep = 0
            self._sweep(now)

        recent = [t for t in self._requests.get(client_ip, []) if t > now - self.window]

        if self.max_requests <= 0 or len(recent) >= self.max_requests:
            self._requests[client_ip] = recent
            oldest = recent[0] if recent else now
            retry_after = max(1, int(oldest + self.window - now) + 1)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Try again later."},
                headers={"Retry-After": str(retry_after)},
            )

        recent.append(now)
        self._requests[client_ip] = recent
        return await call_next(request)
