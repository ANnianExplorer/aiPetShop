"""HTTP 契约：SSE 事件顺序、鉴权、越权、续传。全部走 ASGI，不启端口。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
from conftest import AUTH_HEADERS, make_http, make_settings, parse_sse

from app.api import create_app
from app.core.errors import ModelError
from app.llm import LLMReply, ScriptedModel, ToolCall
from app.storage import InMemoryRepository


async def build_client(
    model: ScriptedModel,
    *,
    settings: Any = None,
    repo: InMemoryRepository | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(
        settings or make_settings(),
        model=model,
        repo=repo or InMemoryRepository(),
        http_client=make_http(),
    )
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent")


async def chat(client: httpx.AsyncClient, text: str, **body: Any) -> list[dict[str, Any]]:
    response = await client.post(
        "/agent/chat", json={"message": text, **body}, headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    return parse_sse(response.text)


async def test_healthz(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    body = response.json()
    assert body["status"] == "ok"
    assert body["auth_mode"] == "header"
    assert body["graph_ready"] is True
    assert set(body["tools"]) == {
        "get_pet_profile",
        "get_health_summary",
        "search_logs",
        "search_docs",
    }


async def test_chat_requires_token(client: httpx.AsyncClient) -> None:
    response = await client.post("/agent/chat", json={"message": "你好"})
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


async def test_chat_rejects_unknown_field(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/agent/chat", json={"message": "你好", "user_id": "9999"}, headers=AUTH_HEADERS
    )
    assert response.status_code == 422  # pydantic extra=forbid，越权字段直接拒


async def test_l1_stream_order(client: httpx.AsyncClient) -> None:
    events = await chat(client, "你好")
    assert [e["event"] for e in events] == ["route", "delta", "delta", "done"]
    assert [e["id"] for e in events] == [1, 2, 3, 4]

    route = events[0]["data"]
    assert (route["route"], route["intent"], route["reason"]) == ("L1", "chat", "greeting")

    done = events[-1]["data"]
    assert done["answer"] == "我在呢。"
    assert done["usage"] == {"prompt_tokens": 10, "completion_tokens": 4}


async def test_session_messages_roundtrip(client: httpx.AsyncClient) -> None:
    events = await chat(client, "你好")
    session_id = events[0]["data"]["session_id"]

    response = await client.get(
        f"/agent/sessions/{session_id}/messages", headers=AUTH_HEADERS
    )
    body = response.json()
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]
    assert body["messages"][0]["content"] == "你好"


async def test_other_user_cannot_read_session(client: httpx.AsyncClient) -> None:
    events = await chat(client, "你好")
    session_id = events[0]["data"]["session_id"]

    response = await client.get(
        f"/agent/sessions/{session_id}/messages",
        headers={"satoken": "token-1002", "x-user-id": "1002"},
    )
    assert response.status_code == 404


async def test_foreign_session_returns_forbidden_event(client: httpx.AsyncClient) -> None:
    events = await chat(client, "你好")
    session_id = events[0]["data"]["session_id"]

    response = await client.post(
        "/agent/chat",
        json={"message": "继续", "session_id": session_id},
        headers={"satoken": "token-1002", "x-user-id": "1002"},
    )
    body = parse_sse(response.text)
    assert body[-1]["event"] == "error"
    assert body[-1]["data"]["code"] == "forbidden"


async def test_replay_run_events(client: httpx.AsyncClient) -> None:
    events = await chat(client, "你好")
    run_id = events[0]["data"]["run_id"]

    full = parse_sse(
        (await client.get(f"/agent/runs/{run_id}/events", headers=AUTH_HEADERS)).text
    )
    assert [e["event"] for e in full] == ["route", "delta", "delta", "done"]

    rest = parse_sse(
        (
            await client.get(
                f"/agent/runs/{run_id}/events", headers=AUTH_HEADERS, params={"after": 2}
            )
        ).text
    )
    assert [e["event"] for e in rest] == ["delta", "done"]

    # Last-Event-ID 与 after 等价
    by_header = parse_sse(
        (
            await client.get(
                f"/agent/runs/{run_id}/events",
                headers={**AUTH_HEADERS, "Last-Event-ID": "3"},
            )
        ).text
    )
    assert [e["event"] for e in by_header] == ["done"]

    denied = await client.get(
        f"/agent/runs/{run_id}/events",
        headers={"satoken": "token-1002", "x-user-id": "1002"},
    )
    assert denied.status_code == 404


async def test_l2_end_to_end_with_tool() -> None:
    model = ScriptedModel(
        replies=[
            LLMReply(
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="search_logs",
                        arguments={"keyword": "疫苗"},
                        raw_arguments='{"keyword": "疫苗"}',
                    )
                ]
            ),
            LLMReply(text="9 月 1 日打过加强针。"),
        ]
    )
    async with await build_client(model) as client:
        events = await chat(client, "上次疫苗是什么时候")

    assert [e["event"] for e in events] == ["route", "tool", "delta", "delta", "done"]
    tool_event = events[1]["data"]
    assert (tool_event["name"], tool_event["status"]) == ("search_logs", "ok")

    done = events[-1]["data"]
    assert done["route"] == "L2"
    assert [c["kind"] for c in done["citations"]] == ["log"]
    assert [s["kind"] for s in done["steps"]] == ["route", "llm", "tool", "llm"]


async def test_stream_failure_emits_error_event() -> None:
    repo = InMemoryRepository()
    model = ScriptedModel(fail_stream=ModelError("上游 429"))
    async with await build_client(model, repo=repo) as client:
        events = await chat(client, "你好")

    assert events[-1]["event"] == "error"
    assert events[-1]["data"]["code"] == "model_error"
    assert events[-1]["data"]["retryable"] is True

    run_id = events[0]["data"]["run_id"]
    record = repo.run_record(run_id)
    assert record["status"].value == "failed"


async def test_model_not_configured() -> None:
    settings = make_settings(llm_api_key="")
    app = create_app(settings, repo=InMemoryRepository(), http_client=make_http())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as client:
        response = await client.post(
            "/agent/chat", json={"message": "你好"}, headers=AUTH_HEADERS
        )
    events = parse_sse(response.text)
    assert events[-1]["event"] == "error"
    assert events[-1]["data"]["code"] == "model_not_configured"


async def test_empty_message_rejected(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/agent/chat", json={"message": "   "}, headers=AUTH_HEADERS
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_request"


# ---------------------------------------------------------------- P1 配额 / 用量 / 记忆

async def test_rate_limit_returns_429_with_retry_after() -> None:
    settings = make_settings(rate_limit_per_minute=1, rate_limit_per_day=10)
    model = ScriptedModel()
    async with await build_client(model, settings=settings) as client:
        first = await client.post(
            "/agent/chat", json={"message": "hello"}, headers=AUTH_HEADERS
        )
        assert first.status_code == 200
        assert first.headers["x-ratelimit-limit"] == "1"
        assert first.headers["x-ratelimit-remaining"] == "0"

        second = await client.post(
            "/agent/chat", json={"message": "hello again"}, headers=AUTH_HEADERS
        )

    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"
    assert int(second.headers["Retry-After"]) >= 1
    assert second.json()["detail"]["scope"] == "chat"


async def test_usage_endpoint_aggregates_succeeded_runs() -> None:
    model = ScriptedModel()
    async with await build_client(model) as client:
        await chat(client, "hi")
        await chat(client, "hi again")
        response = await client.get("/agent/usage/me?days=7", headers=AUTH_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 7
    assert body["runs"] == 2
    assert body["prompt_tokens"] == 20
    assert body["completion_tokens"] == 8
    assert body["total_tokens"] == 28


async def test_recalled_memory_is_injected_into_system_prompt() -> None:
    from app.domain.models import MemoryFact

    repo = InMemoryRepository()
    await repo.upsert_memory_fact(
        MemoryFact(id="", user_id="1001", pet_id=None, key="allergy", value="\u725b\u5976", confidence=0.95)
    )
    model = ScriptedModel()
    async with await build_client(model, repo=repo) as client:
        await chat(client, "\u5b83\u5bf9\u4ec0\u4e48\u8fc7\u654f")

    system = model.stream_calls[0][0]
    assert system["role"] == "system"
    assert "\u8fc7\u654f\uff1a\u725b\u5976" in system["content"]


async def test_conversation_learns_fact_for_next_turn() -> None:
    repo = InMemoryRepository()
    model = ScriptedModel()
    async with await build_client(model, repo=repo) as client:
        events = await chat(client, "\u5b83\u53ebLumina\uff0c\u5bf9\u725b\u5976\u8fc7\u654f")
        session_id = events[0]["data"]["session_id"]
        await chat(client, "\u5b83\u5bf9\u4ec0\u4e48\u8fc7\u654f", session_id=session_id)

    facts = await repo.list_memory_facts("1001", None)
    assert {f.key: f.value for f in facts} == {"pet_name": "Lumina", "allergy": "\u725b\u5976"}
    assert "\u8fc7\u654f\uff1a\u725b\u5976" in model.stream_calls[-1][0]["content"]

async def test_memory_endpoint_lists_learned_facts() -> None:
    repo = InMemoryRepository()
    model = ScriptedModel()
    async with await build_client(model, repo=repo) as client:
        await chat(client, "\u5b83\u53ebLumina\uff0c\u5bf9\u725b\u5976\u8fc7\u654f")
        response = await client.get("/agent/memory/me", headers=AUTH_HEADERS)

    assert response.status_code == 200
    body = response.json()
    facts = {f["key"]: f["value"] for f in body["facts"]}
    assert facts == {"pet_name": "Lumina", "allergy": "\u725b\u5976"}
    assert {f["label"] for f in body["facts"]} == {"\u5ba0\u7269\u540d\u5b57", "\u8fc7\u654f"}
    assert all(0 < f["confidence"] <= 1 for f in body["facts"])


async def test_memory_endpoint_requires_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/agent/memory/me")
    assert response.status_code == 401