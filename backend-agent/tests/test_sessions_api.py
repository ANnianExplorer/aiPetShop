"""`GET /agent/sessions`：App 历史入口。

这条接口的价值不是"能列出会话"，而是**只列出自己的**：
- 没有 token → 401；
- 别人的会话不会出现在列表里（隔离由 `user_id` 过滤保证，不靠前端藏）；
- 排序按最后活跃时间，用户看到的第一条就是刚聊过的；
- 分页的 `total` 是全量，不是当前页条数。
"""

from __future__ import annotations

from typing import Any

import httpx
from conftest import AUTH_HEADERS, make_http, make_settings, parse_sse

from app.api import create_app
from app.llm import ScriptedModel
from app.storage import InMemoryRepository


async def build_client() -> httpx.AsyncClient:
    app = create_app(
        make_settings(),
        model=ScriptedModel(),
        repo=InMemoryRepository(),
        http_client=make_http(),
    )
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent")


async def chat(client: httpx.AsyncClient, text: str, headers: dict[str, str], **body: Any) -> str:
    response = await client.post(
        "/agent/chat", json={"message": text, **body}, headers=headers
    )
    assert response.status_code == 200
    events = parse_sse(response.text)
    route = next(e for e in events if e["event"] == "route")
    return route["data"]["session_id"]


async def test_sessions_requires_token() -> None:
    async with await build_client() as client:
        response = await client.get("/agent/sessions")
    assert response.status_code == 401


async def test_lists_own_sessions_newest_first() -> None:
    async with await build_client() as client:
        older = await chat(client, "你好呀", AUTH_HEADERS)
        newer = await chat(client, "今天天气不错", AUTH_HEADERS)

        response = await client.get("/agent/sessions", headers=AUTH_HEADERS)
        assert response.status_code == 200
        body = response.json()

    assert body["total"] == 2
    assert body["page"] == 1
    ids = [item["id"] for item in body["items"]]
    assert ids == [newer, older], "最后活跃的会话排在最前"
    assert all("user_id" not in item for item in body["items"])


async def test_sessions_are_isolated_by_user() -> None:
    other = {"satoken": "token-2002", "x-user-id": "2002"}

    async with await build_client() as client:
        mine = await chat(client, "我是 1001", AUTH_HEADERS)
        theirs = await chat(client, "我是 2002", other)

        mine_body = (await client.get("/agent/sessions", headers=AUTH_HEADERS)).json()
        theirs_body = (await client.get("/agent/sessions", headers=other)).json()

    assert [i["id"] for i in mine_body["items"]] == [mine]
    assert [i["id"] for i in theirs_body["items"]] == [theirs]


async def test_message_count_and_pagination() -> None:
    async with await build_client() as client:
        session_id = await chat(client, "你好", AUTH_HEADERS)
        # 同会话第二轮：message_count 应该变成 4（2 轮 × user+assistant）
        await chat(client, "再说一句", AUTH_HEADERS, session_id=session_id)
        await chat(client, "另一个会话", AUTH_HEADERS)

        first = (await client.get("/agent/sessions?page=1&page_size=1", headers=AUTH_HEADERS)).json()
        second = (await client.get("/agent/sessions?page=2&page_size=1", headers=AUTH_HEADERS)).json()
        all_items = (await client.get("/agent/sessions?page_size=10", headers=AUTH_HEADERS)).json()

    assert first["total"] == 2 and len(first["items"]) == 1
    assert second["total"] == 2 and len(second["items"]) == 1
    assert first["items"][0]["id"] != second["items"][0]["id"]

    by_id = {item["id"]: item for item in all_items["items"]}
    assert by_id[session_id]["message_count"] == 4
