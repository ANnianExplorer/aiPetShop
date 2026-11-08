"""画像：规则聚合 + 版本仓储 + HTTP 契约。

三类断言分开：
- `build_profile` 是纯函数：把「事实 → 文档」的规则钉死，不碰 IO；
- 仓储：版本递增 / 唯一键 / 裁剪 / 最新事实时间（内存与 MySQL 共用一套断言）；
- HTTP：只返回本人、admin 才能查别人、没有画像给 404 而不是空文档。
"""

from __future__ import annotations

import httpx
import pytest
from conftest import AUTH_HEADERS

from app.domain.models import MemoryFact, ProfileSnapshot
from app.profile import ProfileService, build_profile, profile_lines
from app.storage import InMemoryRepository
from app.storage.memory import InMemoryRepository as _Memory

ADMIN_HEADERS = {"satoken": "token-admin", "x-user-id": "9001", "x-user-role": "admin"}


def _fact(key: str, value: str, *, confidence: float = 0.9, fid: str = "1",
          updated: str = "2026-09-01 10:00:00") -> MemoryFact:
    return MemoryFact(
        id=fid, user_id="1001", pet_id=None, key=key, value=value,
        confidence=confidence, source="conversation",
        create_time=updated, update_time=updated,
    )


# ------------------------------------------------------------------ builder
def test_builds_basics_and_parses_weight() -> None:
    built = build_profile(
        [
            _fact("pet_name", "Lumina"),
            _fact("pet_age", "3岁"),
            _fact("pet_weight", "4.6kg"),
        ]
    )
    basics = built["data"]["basics"]
    assert basics == {"name": "Lumina", "age": "3岁", "weightKg": 4.6}


def test_weight_in_jin_is_halved() -> None:
    built = build_profile([_fact("pet_weight", "9.2斤")])
    assert built["data"]["basics"]["weightKg"] == 4.6


def test_unparsable_weight_kept_as_text() -> None:
    built = build_profile([_fact("pet_weight", "挺重的")])
    assert built["data"]["basics"] == {"weightText": "挺重的"}


def test_allergy_becomes_risk_with_evidence() -> None:
    built = build_profile([_fact("allergy", "牛奶", fid="f-1")])
    risk = built["data"]["riskFlags"][0]
    assert risk["text"] == "对牛奶过敏"
    assert risk["evidence"]["factId"] == "f-1"
    evidence = built["data"]["evidence"]
    assert any(item["key"] == "allergy" and item["factId"] == "f-1" for item in evidence)


def test_missing_facts_do_not_invent_fields() -> None:
    built = build_profile([_fact("pet_name", "Lumina")])
    data = built["data"]
    assert "riskFlags" not in data and "careGaps" not in data and "preferences" not in data
    assert built["fact_count"] == 1


def test_low_confidence_ignored() -> None:
    built = build_profile([_fact("allergy", "牛奶", confidence=0.5)])
    assert built["fact_count"] == 0
    assert "riskFlags" not in built["data"]


def test_highest_confidence_wins_same_key() -> None:
    built = build_profile(
        [_fact("pet_weight", "4kg", confidence=0.75), _fact("pet_weight", "4.6kg", confidence=0.95)]
    )
    assert built["data"]["basics"]["weightKg"] == 4.6


def test_stale_vaccine_becomes_care_gap() -> None:
    from datetime import datetime

    built = build_profile(
        [_fact("vaccine", "猫三联", updated="2025-01-01 10:00:00")],
        now=datetime(2026, 9, 1, 12, 0, 0),
        vaccine_stale_days=300,
    )
    assert "careGaps" in built["data"]


def test_fresh_vaccine_is_not_gap() -> None:
    from datetime import datetime

    built = build_profile(
        [_fact("vaccine", "猫三联", updated="2026-08-01 10:00:00")],
        now=datetime(2026, 9, 1, 12, 0, 0),
    )
    assert "careGaps" not in built["data"]


def test_profile_lines_only_risk_and_gap() -> None:
    assert profile_lines({"basics": {"name": "Lumina"}}) == []
    lines = profile_lines(
        {
            "riskFlags": [{"text": "对牛奶过敏"}],
            "careGaps": [{"text": "疫苗过期"}],
            "basics": {"name": "Lumina"},
        }
    )
    assert lines == ["风险：对牛奶过敏", "待办：疫苗过期"]


# ------------------------------------------------------------------ repository
async def test_profile_version_sequence_and_prune() -> None:
    repo = _Memory()
    first = await repo.save_profile_snapshot(
        ProfileSnapshot(id="1", user_id="1001", pet_id=None, version=1, data={})
    )
    assert first.create_time
    assert await repo.next_profile_version("1001", None) == 2

    await repo.save_profile_snapshot(
        ProfileSnapshot(id="2", user_id="1001", pet_id=None, version=2, data={"v": 2})
    )
    latest = await repo.latest_profile_snapshot("1001", None)
    assert latest is not None and latest.version == 2

    with pytest.raises(ValueError):
        await repo.save_profile_snapshot(
            ProfileSnapshot(id="3", user_id="1001", pet_id=None, version=2, data={})
        )

    for version in (3, 4):
        await repo.save_profile_snapshot(
            ProfileSnapshot(id=str(version), user_id="1001", pet_id=None, version=version, data={})
        )
    assert await repo.prune_profile_versions("1001", None, keep=2) == 2
    versions = await repo.list_profile_versions("1001", None)
    assert [item.version for item in versions] == [4, 3]


async def test_latest_memory_update_tracks_facts() -> None:
    repo = _Memory()
    assert await repo.latest_memory_update("1001", None) is None
    saved = await repo.upsert_memory_fact(_fact("pet_name", "Lumina"))
    # 仓储负责生成更新时间，调用方传的时间不作为准（与 MySQL 的 NOW() 对齐）
    assert await repo.latest_memory_update("1001", None) == saved.update_time


async def test_mysql_profile_contract_if_available() -> None:
    import os

    dsn = os.getenv("PET_AGENT_TEST_MYSQL_DSN")
    if not dsn:
        pytest.skip("未设置 PET_AGENT_TEST_MYSQL_DSN")
    from app.core.ids import new_id
    from app.storage.mysql import MySqlRepository

    repo = MySqlRepository(dsn)
    # 真机会留下数据：每次用全新的 user_id，结束后清掉，避免第二次运行撞唯一键
    user = str(new_id())
    try:
        await repo.ping()
        first = await repo.save_profile_snapshot(
            ProfileSnapshot(id=str(new_id()), user_id=user, pet_id=None, version=1, data={"a": 1})
        )
        assert first.version == 1
        latest = await repo.latest_profile_snapshot(user, None)
        assert latest is not None and latest.data == {"a": 1}
        with pytest.raises(ValueError):
            await repo.save_profile_snapshot(
                ProfileSnapshot(id=str(new_id()), user_id=user, pet_id=None, version=1, data={})
            )
        assert await repo.prune_profile_versions(user, None, keep=1) == 0
    finally:
        async with await repo._ensure_pool() as pool:  # type: ignore[attr-defined]
            async with pool.acquire() as conn, conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM profile_snapshot WHERE user_id=%s", (int(user),)
                )
        await repo.aclose()


# ------------------------------------------------------------------ HTTP
async def _seed_memory(repo: InMemoryRepository, user_id: str = "1001") -> None:
    await repo.upsert_memory_fact(_fact("pet_name", "Lumina", fid="f1"))
    await repo.upsert_memory_fact(_fact("allergy", "牛奶", fid="f2"))


@pytest.mark.asyncio
async def test_profile_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.get("/agent/profile/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_profile_404_before_first_rebuild(client: httpx.AsyncClient) -> None:
    resp = await client.get("/agent/profile/me", headers=AUTH_HEADERS)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refresh_builds_profile_from_facts(
    client: httpx.AsyncClient, repo: InMemoryRepository
) -> None:
    await _seed_memory(repo)
    resp = await client.post("/agent/profile/me/refresh", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == 1
    assert body["fact_count"] == 2
    assert body["data"]["basics"]["name"] == "Lumina"
    assert body["stale"] is False

    again = await client.get("/agent/profile/me", headers=AUTH_HEADERS)
    assert again.status_code == 200
    assert again.json()["version"] == 1


@pytest.mark.asyncio
async def test_profile_marks_stale_when_new_fact_arrives(
    client: httpx.AsyncClient, repo: InMemoryRepository
) -> None:
    await _seed_memory(repo)
    await client.post("/agent/profile/me/refresh", headers=AUTH_HEADERS)
    await repo.upsert_memory_fact(_fact("pet_weight", "4.6kg", fid="f3", updated="2026-12-01 00:00:00"))
    resp = await client.get("/agent/profile/me", headers=AUTH_HEADERS)
    assert resp.json()["stale"] is True


@pytest.mark.asyncio
async def test_admin_can_read_others_profile(client: httpx.AsyncClient, repo: InMemoryRepository) -> None:
    await _seed_memory(repo)
    await client.post("/agent/profile/me/refresh", headers=AUTH_HEADERS)

    denied = await client.get("/agent/admin/profile?user_id=1001", headers=AUTH_HEADERS)
    assert denied.status_code == 403

    resp = await client.get("/agent/admin/profile?user_id=1001", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "1001"

    versions = await client.get("/agent/admin/profile/versions?user_id=1001", headers=ADMIN_HEADERS)
    assert versions.status_code == 200
    assert versions.json()["total"] == 1


@pytest.mark.asyncio
async def test_admin_profile_404_for_unknown_user(client: httpx.AsyncClient) -> None:
    resp = await client.get("/agent/admin/profile?user_id=42", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_service_debounces_rebuild() -> None:
    repo = _Memory()
    clock = {"now": 100.0}
    service = ProfileService(repo, refresh_ttl_s=60, clock=lambda: clock["now"])
    assert service.should_refresh("1001", None) is True
    await repo.upsert_memory_fact(_fact("pet_name", "Lumina"))
    await service.rebuild("1001", None)
    assert service.should_refresh("1001", None) is False
    clock["now"] = 200.0
    assert service.should_refresh("1001", None) is True
