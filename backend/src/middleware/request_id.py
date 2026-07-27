from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from src.logging_config import request_id_var

HEADER_NAME = "X-Request-ID"
MAX_LENGTH = 64


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        incoming = (request.headers.get(HEADER_NAME) or "").strip()
        request_id = incoming[:MAX_LENGTH] if incoming.isascii() and incoming else uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers[HEADER_NAME] = request_id
        return response
