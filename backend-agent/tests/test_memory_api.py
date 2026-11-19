"""B7：记忆可导出、可删除，且严格限定本人。

接口层验证（仓储细节由 `test_repository_contract.py` 的契约测试覆盖）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from conftest import AUTH_HEADERS, make_http, make_settings

from app.api.app import create_app
from app.domain.models import MemoryEpisode, MemoryFact
from app.llm.fake import ScriptedModel
from app.storage.memory import InMemoryRepository

OTHER_HEADERS = {"satoken": "token-2002", "x-user-id": "2002"}


@pytest.fixture
async def ctx() -> AsyncIterator[tuple[httpx.AsyncClient, InMemoryRepository]]:
    repo = InMemoryRepository()
    app = create_app(make_settings(), model=ScriptedModel(), repo=repo, http_client=make_http())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        yield http, repo


async def _seed(repo: InMemoryRepository, user_id: str = "1001") -> None:
    for key, value in (("pet_name", "Lumina"), ("allergy", "牛奶")):
        await repo.upsert_memory_fact(
            MemoryFact(id="", user_id=user_id, key=key, value=value, confidence=0.9)
        )


async def _seed_episode(
    repo: InMemoryRepository, user_id: str = "1001", pet_id: str | None = None
) -> MemoryEpisode:
    return await repo.add_memory_episode(
        MemoryEpisode(
            id="",
            user_id=user_id,
            pet_id=pet_id,
            summary="上周给豆豆洗澡了",
            occurred_at="2026-11-12 00:00:00",
            kind="bath",
            source_message_id="9001",
        )
    )


async def test_export_is_empty_for_new_user(ctx) -> None:
    client, _repo = ctx
    response = await client.get("/agent/memory/me/export", headers=AUTH_HEADERS)
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == 2
    assert payload["facts"] == []
    assert payload["episodes"] == []


async def test_export_contains_labels_and_values(ctx) -> None:
    client, repo = ctx
    await _seed(repo)
    await _seed_episode(repo)
    payload = (await client.get("/agent/memory/me/export", headers=AUTH_HEADERS)).json()
    facts = {item["key"]: item for item in payload["facts"]}
    assert facts["pet_name"]["value"] == "Lumina"
    assert facts["pet_name"]["label"] == "宠物名字"
    assert facts["allergy"]["label"] == "过敏"
    assert payload["episodes"][0]["label"] == "洗澡"
    assert payload["episodes"][0]["source_message_id"] == "9001"


async def test_episodes_endpoint_lists_and_deletes(ctx) -> None:
    client, repo = ctx
    episode = await _seed_episode(repo)

    listed = await client.get("/agent/memory/me/episodes", headers=AUTH_HEADERS)
    assert listed.status_code == 200
    body = listed.json()
    assert [item["id"] for item in body["episodes"]] == [episode.id]
    assert body["episodes"][0]["occurred_at"] == "2026-11-12 00:00:00"

    deleted = await client.delete(
        f"/agent/memory/me/episodes/{episode.id}", headers=AUTH_HEADERS
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "id": episode.id}
    assert (await client.get("/agent/memory/me/episodes", headers=AUTH_HEADERS)).json()[
        "episodes"
    ] == []

    again = await client.delete(
        f"/agent/memory/me/episodes/{episode.id}", headers=AUTH_HEADERS
    )
    assert again.status_code == 404


async def test_episodes_are_isolated_between_users(ctx) -> None:
    client, repo = ctx
    episode = await _seed_episode(repo)

    other = await client.get("/agent/memory/me/episodes", headers=OTHER_HEADERS)
    assert other.json()["episodes"] == []
    denied = await client.delete(
        f"/agent/memory/me/episodes/{episode.id}", headers=OTHER_HEADERS
    )
    assert denied.status_code == 404

    mine = await client.get("/agent/memory/me/episodes", headers=AUTH_HEADERS)
    assert len(mine.json()["episodes"]) == 1


async def test_delete_then_export_is_empty(ctx) -> None:
    client, repo = ctx
    await _seed(repo)

    deleted = await client.delete(
        "/agent/memory/me", params={"key": "allergy"}, headers=AUTH_HEADERS
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "key": "allergy"}

    payload = (await client.get("/agent/memory/me/export", headers=AUTH_HEADERS)).json()
    assert [item["key"] for item in payload["facts"]] == ["pet_name"]

    again = await client.delete(
        "/agent/memory/me", params={"key": "allergy"}, headers=AUTH_HEADERS
    )
    assert again.status_code == 404


async def test_memory_is_isolated_between_users(ctx) -> None:
    client, repo = ctx
    await _seed(repo)

    # 别人导出看不到、删不动
    other_export = (await client.get("/agent/memory/me/export", headers=OTHER_HEADERS)).json()
    assert other_export["facts"] == []
    denied = await client.delete(
        "/agent/memory/me", params={"key": "allergy"}, headers=OTHER_HEADERS
    )
    assert denied.status_code == 404

    # 原用户的数据仍在
    mine = (await client.get("/agent/memory/me/export", headers=AUTH_HEADERS)).json()
    assert len(mine["facts"]) == 2


async def test_memory_endpoints_require_token(ctx) -> None:
    client, _repo = ctx
    assert (await client.get("/agent/memory/me/export")).status_code == 401
    assert (await client.delete("/agent/memory/me", params={"key": "x"})).status_code == 401
    assert (await client.get("/agent/memory/me/episodes")).status_code == 401
    assert (await client.delete("/agent/memory/me/episodes/1")).status_code == 401
