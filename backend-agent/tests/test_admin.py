"""管理端只读接口：权限、列表、详情轨迹、全局用量。

最要紧的两条不变量：
- 非管理员一律 403，且 backend 模式下**伪造 `x-user-role` 无效**（角色只信后端）；
- 管理员看他人会话必须留 `admin.access` 审计日志（只记关系，不记内容）。
"""

from __future__ import annotations

import logging

import httpx
import pytest
from conftest import AUTH_HEADERS, make_http, make_settings

from app.api import create_app
from app.llm import ScriptedModel
from app.storage import InMemoryRepository
from app.tasks import (
    TOPIC_AUDIT_TOOL,
    TOPIC_DOC_INGEST,
    TOPIC_MEMORY_OBSERVE,
    InProcessTaskQueue,
)

ADMIN_HEADERS = {"satoken": "token-admin", "x-user-id": "9001", "x-user-role": "admin"}


async def _chat(client: httpx.AsyncClient, headers: dict[str, str], text: str = "你好呀") -> str:
    """发一条 L1 消息并返回会话 id（从 route 事件里取）。"""
    resp = await client.post(
        "/agent/chat", json={"message": text, "channel": "app"}, headers=headers
    )
    assert resp.status_code == 200
    for block in resp.text.split("\n\n"):
        if "event: route" in block:
            for line in block.splitlines():
                if line.startswith("data: "):
                    import json

                    return json.loads(line[6:])["session_id"]
    raise AssertionError("没有收到 route 事件")


@pytest.mark.asyncio
async def test_non_admin_forbidden(client: httpx.AsyncClient) -> None:
    resp = await client.get("/agent/admin/sessions", headers=AUTH_HEADERS)
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


@pytest.mark.asyncio
async def test_missing_token_unauthorized(client: httpx.AsyncClient) -> None:
    resp = await client.get("/agent/admin/sessions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_lists_and_filters(client: httpx.AsyncClient) -> None:
    sid = await _chat(client, AUTH_HEADERS, "我家猫今天有点打喷嚏")

    resp = await client.get("/agent/admin/sessions?user_id=1001", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == sid
    assert body["items"][0]["message_count"] >= 2

    # 关键词不匹配时列表为空，说明过滤真的生效（不是回全量）
    miss = await client.get("/agent/admin/sessions?q=不存在的标题", headers=ADMIN_HEADERS)
    assert miss.json()["total"] == 0


@pytest.mark.asyncio
async def test_admin_detail_has_messages_and_steps(client: httpx.AsyncClient) -> None:
    sid = await _chat(client, AUTH_HEADERS)

    resp = await client.get(f"/agent/admin/sessions/{sid}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["messages"]) >= 2
    assert body["runs"], "至少有一次运行"
    run = body["runs"][-1]
    assert run["route"] == "L1"
    assert run["steps"], "步骤轨迹必须落库，否则管理端看不见它做了什么"
    assert run["steps"][0]["kind"] == "route"


@pytest.mark.asyncio
async def test_admin_detail_unknown_session_404(client: httpx.AsyncClient) -> None:
    resp = await client.get("/agent/admin/sessions/1794000000000000999", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_detail_writes_audit_log(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    sid = await _chat(client, AUTH_HEADERS)
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="agent.admin"):
        resp = await client.get(f"/agent/admin/sessions/{sid}", headers=ADMIN_HEADERS)
    assert resp.status_code == 200

    rec = next((r for r in caplog.records if r.getMessage().startswith("admin.access")), None)
    assert rec is not None
    ctx = getattr(rec, "ctx", {})
    assert ctx["admin_id"] == "9001"
    assert ctx["target_user"] == "1001"
    assert ctx["session_id"] == sid
    # 审计里不能出现消息正文
    assert "你好呀" not in str(ctx)


@pytest.mark.asyncio
async def test_admin_usage_overview(client: httpx.AsyncClient) -> None:
    await _chat(client, AUTH_HEADERS)

    resp = await client.get("/agent/admin/usage?days=7", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["runs"] == 1
    assert body["users"] == 1
    assert body["total_tokens"] >= 0
    assert isinstance(body["by_day"], list)


@pytest.mark.asyncio
async def test_admin_memory_requires_admin_and_returns_facts(
    client: httpx.AsyncClient,
) -> None:
    """管理员能看别人记住了什么；普通用户看自己的记忆只能走 /agent/memory/me。"""
    await _chat(client, AUTH_HEADERS, "我家猫叫Lumina，对牛奶过敏")

    denied = await client.get("/agent/admin/memory?user_id=1001", headers=AUTH_HEADERS)
    assert denied.status_code == 403

    resp = await client.get("/agent/admin/memory?user_id=1001", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    keys = {f["key"] for f in resp.json()["facts"]}
    assert "allergy" in keys
    assert "pet_name" in keys


@pytest.mark.asyncio
async def test_forged_header_role_is_ignored_in_backend_mode() -> None:
    """backend 模式：角色来自 /auth/current（user），请求头写 admin 也不放行。"""
    app = create_app(
        make_settings(auth_mode="backend"),
        model=ScriptedModel(),
        repo=InMemoryRepository(),
        http_client=make_http(),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        resp = await http.get(
            "/agent/admin/sessions",
            headers={"satoken": "token-1001", "x-user-id": "9001", "x-user-role": "admin"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_tasks_reports_disabled_when_backend_off(
    client: httpx.AsyncClient,
) -> None:
    """`TASK_BACKEND=off` 不是故障：要能一眼看出「没启用」，而不是以为队列空了。"""
    denied = await client.get("/agent/admin/tasks", headers=AUTH_HEADERS)
    assert denied.status_code == 403

    resp = await client.get("/agent/admin/tasks", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["backend"] == "off"
    assert {t["topic"] for t in body["topics"]} == {
        TOPIC_MEMORY_OBSERVE,
        TOPIC_AUDIT_TOOL,
        TOPIC_DOC_INGEST,
    }


@pytest.mark.asyncio
async def test_admin_replays_dead_letters(settings) -> None:
    """死信要能被放回队列重试，且 attempt 归零——否则一失败又立刻进死信。"""
    queue = InProcessTaskQueue(topic=TOPIC_AUDIT_TOOL, max_attempts=2)
    # 造一条死信：取出来两次都 nack
    await queue.publish(TOPIC_AUDIT_TOOL, key="run:tool", payload={"name": "get_pet_profile"})
    for _ in range(2):
        message = await queue.receive(TOPIC_AUDIT_TOOL, timeout_s=0.05)
        assert message is not None
        await queue.nack(message, error="boom")

    app = create_app(
        settings,
        model=ScriptedModel(),
        repo=InMemoryRepository(),
        http_client=make_http(),
        task_queue=queue,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        before = await http.get("/agent/admin/tasks", headers=ADMIN_HEADERS)
        assert before.json()["enabled"] is True
        dead_before = {t["topic"]: t["dead_letters"] for t in before.json()["topics"]}
        assert dead_before[TOPIC_AUDIT_TOOL] == 1

        denied = await http.post(
            "/agent/admin/tasks/dead-letters/replay",
            json={"topic": TOPIC_AUDIT_TOOL},
            headers=AUTH_HEADERS,
        )
        assert denied.status_code == 403

        replay = await http.post(
            "/agent/admin/tasks/dead-letters/replay",
            json={"topic": TOPIC_AUDIT_TOOL},
            headers=ADMIN_HEADERS,
        )
        assert replay.status_code == 200
        assert replay.json() == {"topic": TOPIC_AUDIT_TOOL, "replayed": 1}

        after = await http.get("/agent/admin/tasks", headers=ADMIN_HEADERS)
        dead_after = {t["topic"]: t["dead_letters"] for t in after.json()["topics"]}
        assert dead_after[TOPIC_AUDIT_TOOL] == 0

        unknown = await http.post(
            "/agent/admin/tasks/dead-letters/replay",
            json={"topic": "agent.nope"},
            headers=ADMIN_HEADERS,
        )
        assert unknown.status_code == 400

    replayed = await queue.receive(TOPIC_AUDIT_TOOL, timeout_s=0.05)
    assert replayed is not None and replayed.attempt == 1
