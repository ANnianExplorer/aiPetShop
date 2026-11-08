"""请求级可观测：`x-request-id` 透传/生成 + 访问日志 + HTTP 指标。

注意：这里的 `latency_ms` 是「到响应头写出为止」的耗时。SSE 的正文是流式的，
整段回答耗时由 `agent_run.latency_ms` 记录，两者不冲突。
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ..core.logging import log_event, request_id_var
from ..core.metrics import HTTP_DURATION, HTTP_REQUESTS, metrics

access_log = logging.getLogger("agent.access")

MAX_REQUEST_ID_LEN = 64


def _route_template(request: Request) -> str:
    """用路由模板做标签，避免 `/agent/sessions/<19 位 id>` 炸出无限时间序列。"""
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) and path else request.url.path


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = (request.headers.get("x-request-id") or "").strip()[:MAX_REQUEST_ID_LEN]
        request_id = incoming or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        finally:
            elapsed = time.perf_counter() - started
            path = _route_template(request)
            metrics.inc(HTTP_REQUESTS, {"method": request.method, "path": path, "status": str(status)})
            metrics.observe(HTTP_DURATION, elapsed, {"method": request.method, "path": path})
            log_event(
                access_log,
                logging.INFO,
                "http request",
                method=request.method,
                path=request.url.path,
                status=status,
                latency_ms=int(elapsed * 1000),
            )
            request_id_var.reset(token)
