"""熔断器单测：三态迁移、异常计数口径、与 /readyz 的联动。

重点不是"能打开"，而是三个容易写错的地方：
1. 打开后**不发请求**就能快速失败（否则熔断等于没做）；
2. 401/422 这类调用方错误不计入失败（否则一个过期 token 把后端熔断掉）；
3. half_open 只放**一个**探测，防止恢复瞬间被流量打死。
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
from conftest import AUTH_HEADERS, make_http, make_settings

from app.api import create_app
from app.core.circuit import CircuitBreaker, counts_as_failure
from app.core.errors import BackendError, CircuitOpen, ModelError, Unauthorized
from app.llm import ScriptedModel
from app.storage import InMemoryRepository


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


async def _boom() -> None:
    raise BackendError("下游 502")


async def _ok() -> str:
    return "ok"


# ---------------------------------------------------------------- 状态机
async def test_opens_after_threshold_and_fails_fast() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker("backend", threshold=3, cooldown_s=30, clock=clock)
    for _ in range(3):
        with pytest.raises(BackendError):
            await breaker.call(_boom)
    assert breaker.state == "open"

    calls = {"n": 0}

    async def counted() -> str:
        calls["n"] += 1
        return "should-not-run"

    with pytest.raises(CircuitOpen):
        await breaker.call(counted)
    assert calls["n"] == 0, "熔断打开后不能再打到下游"
    assert breaker.snapshot().retry_after_s == pytest.approx(30, abs=1)


async def test_cooldown_half_open_then_close() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker("llm", threshold=2, cooldown_s=10, clock=clock)
    for _ in range(2):
        with pytest.raises(ModelError):
            await breaker.call(_boom_model)
    assert breaker.state == "open"

    clock.advance(11)
    assert breaker.state == "half_open"
    assert await breaker.call(_ok) == "ok"
    assert breaker.state == "closed"


async def test_half_open_probe_failure_reopens() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker("llm", threshold=1, cooldown_s=5, clock=clock)
    with pytest.raises(BackendError):
        await breaker.call(_boom)
    clock.advance(6)
    assert breaker.state == "half_open"
    with pytest.raises(BackendError):
        await breaker.call(_boom)
    assert breaker.state == "open"
    assert breaker.snapshot().trips == 2


async def test_half_open_allows_only_one_probe() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker("llm", threshold=1, cooldown_s=5, clock=clock)
    with pytest.raises(BackendError):
        await breaker.call(_boom)
    clock.advance(6)

    release = asyncio.Event()

    async def slow_probe() -> str:
        await release.wait()
        return "probe"

    task = asyncio.create_task(breaker.call(slow_probe))
    await asyncio.sleep(0)
    with pytest.raises(CircuitOpen):
        await breaker.call(_ok)
    release.set()
    assert await task == "probe"


async def test_client_errors_do_not_trip_breaker() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker("backend", threshold=2, cooldown_s=30, clock=clock)

    async def unauthorized() -> None:
        raise Unauthorized("登录态失效")

    for _ in range(5):
        with pytest.raises(Unauthorized):
            await breaker.call(unauthorized)
    assert breaker.state == "closed", "401 是调用方问题，不该把后端熔断"


def test_counts_as_failure_policy() -> None:
    assert counts_as_failure(BackendError("x")) is True
    assert counts_as_failure(ModelError("x")) is True
    assert counts_as_failure(Unauthorized("x")) is False
    assert counts_as_failure(RuntimeError("boom")) is True


async def _boom_model() -> None:
    raise ModelError("模型 502")


# ---------------------------------------------------------------- 与 /readyz 联动
async def test_readyz_reports_open_circuit() -> None:
    settings = make_settings()
    app = create_app(
        settings,
        model=ScriptedModel(),
        repo=InMemoryRepository(),
        http_client=make_http(),
    )
    breaker: CircuitBreaker = app.state.backend_breaker
    for _ in range(settings.circuit_threshold):
        breaker.record_failure()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        ready = await http.get("/readyz")
        health = await http.get("/healthz", headers=AUTH_HEADERS)

    assert ready.status_code == 503
    body = ready.json()
    assert body["status"] == "degraded"
    assert body["checks"]["circuit:backend"] == "open"
    # liveness 不受熔断影响：进程本身是好的，只是不该接流量
    assert health.status_code == 200
