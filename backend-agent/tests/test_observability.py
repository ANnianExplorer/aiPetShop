"""可观测性契约：request_id、结构化日志、就绪探针（ADR-0007）。"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import pytest
from conftest import AUTH_HEADERS, make_http, make_settings

from app.api import create_app
from app.core.logging import JsonFormatter, log_event, request_id_var
from app.llm import ScriptedModel
from app.storage import InMemoryRepository


async def test_request_id_generated_and_echoed(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    request_id = response.headers.get("x-request-id", "")
    assert len(request_id) == 32
    int(request_id, 16)  # 必须是 uuid4().hex


async def test_request_id_propagated_from_caller(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz", headers={"x-request-id": "trace-abc-123"})
    assert response.headers["x-request-id"] == "trace-abc-123"


async def test_oversized_request_id_is_truncated(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz", headers={"x-request-id": "x" * 200})
    assert len(response.headers["x-request-id"]) == 64


def test_json_formatter_emits_single_line() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.json",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="tool call",
        args=(),
        exc_info=None,
    )
    record.ctx = {"tool": "search_logs", "ok": True, "latency_ms": 7}  # type: ignore[attr-defined]
    token = request_id_var.set("req-42")
    try:
        payload: dict[str, Any] = json.loads(formatter.format(record))
    finally:
        request_id_var.reset(token)

    assert payload["msg"] == "tool call"
    assert payload["tool"] == "search_logs"
    assert payload["latency_ms"] == 7
    assert payload["request_id"] == "req-42"
    assert payload["level"] == "INFO"


def test_log_event_writes_ctx_and_keeps_record_attributes() -> None:
    captured: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    logger = logging.getLogger("test.capture")
    logger.handlers = [Capture()]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_event(logger, logging.INFO, "tool call", tool="search_logs", ok=True)
    assert len(captured) == 1
    # ctx 单独挂在 record 上，不是平铺进 __dict__，避免与保留字段冲突
    assert captured[0].ctx == {"tool": "search_logs", "ok": True}
    assert json.loads(JsonFormatter().format(captured[0]))["tool"] == "search_logs"


def test_log_event_rejects_reserved_field() -> None:
    with pytest.raises(ValueError, match="内置属性"):
        log_event(logging.getLogger("test.json"), logging.INFO, "boom", name="x")


async def test_readyz_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"repo": "ok", "model": "ok"}


async def test_readyz_degrades_when_repo_unavailable(client: httpx.AsyncClient) -> None:
    repo = client.app.state.repo  # type: ignore[attr-defined]

    async def boom() -> None:
        raise ConnectionError("mysql gone")

    repo.ping = boom  # type: ignore[method-assign]
    response = await client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["repo"] == "ConnectionError"
    assert body["checks"]["model"] == "ok"


async def test_readyz_degrades_without_model_key() -> None:
    settings = make_settings(llm_api_key="")
    app = create_app(settings, model=ScriptedModel(), repo=InMemoryRepository(), http_client=make_http())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent") as http:
        response = await http.get("/readyz")
    assert response.status_code == 503
    assert response.json()["checks"]["model"] == "not_configured"


async def test_chat_is_not_blocked_by_observability(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/agent/chat",
        json={"message": "你好", "channel": "app"},
        headers={**AUTH_HEADERS, "x-request-id": "chat-1"},
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "chat-1"
    assert "event: done" in response.text
