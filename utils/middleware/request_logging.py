from fastapi import Request
import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ):
        """Process the request, log it, and return the response."""
        start_time = time.time()

        # Log request
        request_data = {
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers),
            "client_ip": (
                request.client.host
                if request.client
                else None
            ),
        }

        logger.info(
            f"Request started path={request_data['path']} "
            f"method={request_data['method']}",
            extra=request_data,
        )

        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        response_data = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }

        logger.info(
            f"Request completed path={response_data['path']} "
            f"method={response_data['method']} "
            f"status_code={response_data['status_code']} "
            f"duration_ms={response_data['duration_ms']}",
            extra=response_data,
        )

        return response
