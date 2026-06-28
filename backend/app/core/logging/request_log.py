from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.logging.logger import get_logger


_logger = get_logger("request")


async def log_request(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - started) * 1000
    _logger.info("%s %s -> %s %.1fms", request.method, request.url.path, response.status_code, latency_ms)
    response.headers["X-Process-Time-ms"] = f"{latency_ms:.1f}"
    return response
