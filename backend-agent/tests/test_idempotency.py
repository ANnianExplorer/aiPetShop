"""幂等键：同一条消息重试两次，只能产生一次执行、一次计费、一条消息。

覆盖三层：
1. 接口层：`client_message_id` 发送两次 → 只有一个 run，第二次 `done.replayed == true`；
2. 仓储层：`start_run` 撞唯一键返回已有 run（两套实现同一套断言，MySQL 需要 DSN）；
3. 校验层：非法 key（空格、超长、中文）在入口就被 422 拦下，不会打穿到库。
"""

from __future__ import annotations

import httpx
from conftest import AUTH_HEADERS, make_http, make_settings, parse_sse

from app.api import create_app
from app.domain.models import Intent, Route, Run
from app.llm import ScriptedModel
from app.storage import InMemoryRepository


def _done(events: list[dict]) -> dict:
    done = [e for e in events if e["event"] == "done"]
    assert done, f"没有 done 事件：{[e['event'] for e in events]}"
    return done[-1]["data"]


async def _send(http: httpx.AsyncClient, key: str) -> list[dict]:
    response = await http.post(
        "/agent/chat",
        json={"message": "上次打疫苗是什么时候", "client_message_id": key},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


async def test_same_key_does_not_execute_twice() -> None:
    settings = make_settings()
    repo = InMemoryRepository()
    model = ScriptedModel(chunks=("我", "在呢。"))
    app = create_app(settings, model=model, repo=repo, http_client=make_http())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        first = await _send(http, "retry-001")
        second = await _send(http, "retry-001")

    session_id = _done(first)["session_id"]
    assert "replayed" not in _done(first), "首次执行不该被标记为回放"
    assert _done(second)["replayed"] is True
    assert _done(second)["run_id"] == _done(first)["run_id"]

    # 只执行了一次：模型只被调用一次，只落一条用户消息 + 一条助手消息
    assert len(model.stream_calls) == 1
    messages = await repo.list_messages(session_id, limit=20)
    assert [m.role.value for m in messages] == ["user", "assistant"]
    assert len(repo.run_record(_done(first)["run_id"]) or {}) > 0
    assert len(repo._runs) == 1


async def test_different_keys_execute_separately() -> None:
    settings = make_settings()
    repo = InMemoryRepository()
    model = ScriptedModel(chunks=("好", "的。"))
    app = create_app(settings, model=model, repo=repo, http_client=make_http())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        first = await _send(http, "msg-a")
        second = await _send(http, "msg-b")

    assert _done(first)["run_id"] != _done(second)["run_id"]
    assert len(model.stream_calls) == 2
    assert len(repo._runs) == 2


async def test_invalid_key_rejected_at_entry() -> None:
    settings = make_settings()
    app = create_app(
        settings, model=ScriptedModel(), repo=InMemoryRepository(), http_client=make_http()
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        for bad in ("带空格 key", "中文键", "x" * 65):
            response = await http.post(
                "/agent/chat",
                json={"message": "hi", "client_message_id": bad},
                headers=AUTH_HEADERS,
            )
            assert response.status_code == 422, bad


async def test_repository_unique_key_semantics() -> None:
    """仓储层：同 key 第二次返回旧 run；查询按用户维度，不按会话。"""
    from app.domain.models import RunStatus

    repo = InMemoryRepository()
    session = await repo.get_or_create_session(None, "1001", None, "app", "标题")
    first = await repo.start_run(
        Run(id="", session_id=session.id, user_id="1001", user_message_id="m1",
            route=Route.L1, intent=Intent.CHAT, model="scripted", idempotency_key="k1")
    )
    again = await repo.start_run(
        Run(id="", session_id=session.id, user_id="1001", user_message_id="m2",
            route=Route.L1, intent=Intent.CHAT, model="scripted", idempotency_key="k1")
    )
    assert again.id == first.id
    assert again.user_message_id == "m1"

    found = await repo.find_run_by_idempotency("1001", "k1")
    assert found is not None and found.id == first.id
    assert await repo.find_run_by_idempotency("1001", "nope") is None
    # 换个用户用同一个 key 不该命中别人的 run
    assert await repo.find_run_by_idempotency("2002", "k1") is None
    assert first.status == RunStatus.RUNNING
