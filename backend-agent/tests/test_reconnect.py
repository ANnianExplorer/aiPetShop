"""断线重连的底座：运行的生命周期必须独立于 HTTP 连接（计划 S1.23 / BACKLOG B8）。

这批用例守的是四条不变量：
- N1 关掉消费端（= 客户端断网）**不得**取消运行，答案照样跑完、`done` 照样落日志；
- N2 从任意游标 `after` 跟随，事件 id 严格递增、不重不漏，末尾恰好一条终止事件；
- N3 `follow=0` 仍是原来的快照语义；
- N4 幂等回放（同 `client_message_id`）不被后台接管，不会二次执行。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
from conftest import AUTH_HEADERS, make_http, make_settings, parse_sse

from app.api import create_app
from app.domain.events import EventType
from app.domain.models import Role, RunStatus, Usage
from app.llm import ScriptedModel, StreamChunk
from app.runtime import Caller, ChatCommand
from app.runtime.follow import follow_events
from app.storage import InMemoryRepository

SLOW_CHUNKS = ("第一段", "第二段", "第三段")


class SlowModel(ScriptedModel):
    """真实网络里 token 是一点点挤出来的；脚本模型太快，测不出断线窗口。"""

    def __init__(self, *, delay_s: float = 0.05, chunks: tuple[str, ...] = SLOW_CHUNKS) -> None:
        super().__init__(chunks=chunks)
        self._slow_chunks = list(chunks)
        self._slow_usage = Usage(10, 4)
        self._delay = delay_s

    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[StreamChunk]:
        self.stream_calls.append([dict(m) for m in messages])
        for text in self._slow_chunks:
            await asyncio.sleep(self._delay)
            yield StreamChunk(text=text)
        yield StreamChunk(usage=self._slow_usage)


def build_app(
    model: ScriptedModel, *, repo: InMemoryRepository | None = None
) -> tuple[Any, InMemoryRepository]:
    repo = repo or InMemoryRepository()
    app = create_app(make_settings(), model=model, repo=repo, http_client=make_http())
    return app, repo


def client_for(app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    )


async def wait_idle(supervisor: Any, timeout_s: float = 5.0) -> None:
    """等后台运行收场：这是"运行脱离连接"之后唯一可靠的完成信号。"""
    deadline = time.monotonic() + timeout_s
    while supervisor.running():
        if time.monotonic() > deadline:
            raise AssertionError("后台运行超时仍未结束")
        await asyncio.sleep(0.01)


async def test_closing_consumer_does_not_cancel_run() -> None:
    """N1：客户端只拿到 route 就断开，服务端仍要把这一轮跑完。"""
    model = SlowModel(delay_s=0.05)
    app, repo = build_app(model)
    runner = app.state.runner

    agen = runner.stream(ChatCommand(message="你好"), Caller("1001", "token-1001"))
    first = await anext(agen)
    assert first.type is EventType.ROUTE
    run_id = first.data["run_id"]

    await agen.aclose()  # ← 模拟断网：消费端关闭
    await wait_idle(app.state.supervisor)
    await app.state.supervisor.aclose()

    run = await repo.get_run(run_id)
    assert run is not None
    assert run.status is RunStatus.SUCCEEDED, "断线不应把 run 打成 cancelled"

    events = await app.state.eventlog.events(run_id, 0)
    assert [e.type for e in events].count(EventType.DONE) == 1
    assert events[-1].type is EventType.DONE

    messages = await repo.list_messages(run.session_id, limit=10)
    answers = [m.content for m in messages if m.role is Role.ASSISTANT]
    assert answers == ["".join(SLOW_CHUNKS)]


async def test_follow_returns_events_after_cursor() -> None:
    """N2：从中间游标跟随，拿到的是连续的尾部，不重不漏，收在 done。"""
    model = SlowModel(delay_s=0.01)
    app, repo = build_app(model)
    async with client_for(app) as http:
        full = parse_sse(
            (await http.post("/agent/chat", json={"message": "你好"}, headers=AUTH_HEADERS)).text
        )
    run_id = full[0]["data"]["run_id"]

    seen = [e async for e in follow_events(app.state.eventlog, repo, run_id, 2, poll_s=0.01)]
    assert [e.seq for e in seen] == [3, 4, 5]
    assert [e.type for e in seen] == [EventType.DELTA, EventType.DELTA, EventType.DONE]
    assert "".join(e.data["text"] for e in seen if e.type is EventType.DELTA) == "第二段第三段"


async def test_follow_waits_for_running_run() -> None:
    """N2 的房间另一头：run 还在跑时 `follow=1` 要挂到结束，而不是立刻返回半截。"""
    model = SlowModel(delay_s=0.05)
    app, _repo = build_app(model)
    runner = app.state.runner

    agen = runner.stream(ChatCommand(message="你好"), Caller("1001", "token-1001"))
    first = await anext(agen)
    run_id = first.data["run_id"]

    async with client_for(app) as http:
        body = parse_sse(
            (
                await http.get(
                    f"/agent/runs/{run_id}/events",
                    params={"after": first.seq, "follow": 1},
                    headers=AUTH_HEADERS,
                )
            ).text
        )

    assert [e["event"] for e in body] == ["delta", "delta", "delta", "done"]
    assert [e["id"] for e in body] == [2, 3, 4, 5]
    await agen.aclose()
    await app.state.supervisor.aclose()


async def test_snapshot_stays_snapshot_without_follow() -> None:
    """N3：默认不跟随，跑完的 run 无论 follow 与否拿到的都是同一份尾巴。"""
    model = SlowModel(delay_s=0.01)
    app, _repo = build_app(model)
    async with client_for(app) as http:
        full = parse_sse(
            (await http.post("/agent/chat", json={"message": "你好"}, headers=AUTH_HEADERS)).text
        )
        run_id = full[0]["data"]["run_id"]
        plain = parse_sse(
            (
                await http.get(
                    f"/agent/runs/{run_id}/events", params={"after": 2}, headers=AUTH_HEADERS
                )
            ).text
        )
        followed = parse_sse(
            (
                await http.get(
                    f"/agent/runs/{run_id}/events",
                    params={"after": 2, "follow": 1},
                    headers=AUTH_HEADERS,
                )
            ).text
        )

    assert [e["event"] for e in plain] == ["delta", "delta", "done"]
    assert [e["id"] for e in followed] == [e["id"] for e in plain]


async def test_idempotent_replay_still_forwards() -> None:
    """N4：同 key 重试走回放，事件 id 与首次一致，模型只被调用一次。"""
    model = SlowModel(delay_s=0.01)
    app, _repo = build_app(model)
    body = {"message": "你好", "client_message_id": "resume-key-1"}

    async with client_for(app) as http:
        first = parse_sse((await http.post("/agent/chat", json=body, headers=AUTH_HEADERS)).text)
        replay = parse_sse((await http.post("/agent/chat", json=body, headers=AUTH_HEADERS)).text)

    assert [e["id"] for e in replay] == [e["id"] for e in first]
    assert replay[-1]["event"] == "done"
    assert replay[-1]["data"]["replayed"] is True
    assert len(model.stream_calls) == 1
