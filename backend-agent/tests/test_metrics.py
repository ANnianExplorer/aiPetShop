"""B5：最小指标必须真的能被 Prometheus 读到，而不是只写了一个模块。

三个角度：
1. HTTP 指标按「路由模板」记，不是按原始 URL（防高基数）；
2. 跑一轮 L1 对话后 runs/tokens 有值；
3. `/metrics` 输出是合法文本格式，且不含用户内容。
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from conftest import AUTH_HEADERS, make_http, make_settings

from app.api.app import create_app
from app.core.metrics import (
    HTTP_REQUESTS,
    RUNS,
    TOKENS,
    metrics,
)
from app.llm.fake import ScriptedModel
from app.storage.memory import InMemoryRepository


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    metrics.reset()


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    settings = make_settings()
    app = create_app(settings, model=ScriptedModel(), repo=InMemoryRepository(), http_client=make_http())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        yield http


async def test_http_metrics_use_route_template(client: httpx.AsyncClient) -> None:
    """带路径参数的请求必须记成模板，否则每次都是新时间序列。"""
    await client.get("/agent/documents/1794000000000000001", headers=AUTH_HEADERS)
    assert metrics.counter_value(
        HTTP_REQUESTS,
        {"method": "GET", "path": "/agent/documents/{document_id}", "status": "404"},
    ) == 1
    assert metrics.counter_value(
        HTTP_REQUESTS,
        {"method": "GET", "path": "/agent/documents/1794000000000000001", "status": "404"},
    ) == 0


async def test_runs_and_tokens_counted(client: httpx.AsyncClient) -> None:
    async with client.stream(
        "POST",
        "/agent/chat",
        json={"message": "你好"},
        headers=AUTH_HEADERS,
    ) as response:
        await response.aread()

    assert metrics.counter_value(RUNS, {"route": "L1", "status": "succeeded"}) == 1
    assert metrics.counter_value(TOKENS, {"direction": "prompt"}) == 10
    assert metrics.counter_value(TOKENS, {"direction": "completion"}) == 4


async def test_metrics_endpoint_renders_prometheus_text(client: httpx.AsyncClient) -> None:
    await client.get("/healthz")
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "# TYPE pet_agent_http_requests_total counter" in body
    assert 'pet_agent_http_requests_total{method="GET",path="/healthz",status="200"}' in body
    assert "pet_agent_http_request_duration_seconds_count" in body
    # 不含用户内容：指标里不该出现会话/消息正文
    assert "你好" not in body
