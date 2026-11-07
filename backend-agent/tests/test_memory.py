"""记忆层：抽取规则、算子语义、服务写入与召回。"""

from __future__ import annotations

import pytest

from app.domain.models import MemoryFact
from app.memory import MemoryOp, MemoryService, decide, extract, label_of
from app.storage import InMemoryRepository


def test_extract_pet_name_and_allergy() -> None:
    facts = {c.key: c.value for c in extract("我家猫叫Lumina，对牛奶过敏")}
    assert facts["pet_name"] == "Lumina"
    assert facts["allergy"] == "牛奶"


def test_extract_weight_and_age() -> None:
    facts = {c.key: c.value for c in extract("三岁的布偶，现在4.6公斤")}
    assert facts["pet_weight"] == "4.6"
    assert facts["pet_age"] == "3"


def test_extract_food_habits() -> None:
    facts = {c.key: c.value for c in extract("它不吃肝脏，但特别爱吃冻干")}
    assert facts["food_avoid"] == "肝脏"
    assert facts["food_like"] == "冻干"


def test_extract_ignores_small_talk() -> None:
    assert extract("今天天气不错") == []
    assert extract("你好呀") == []
    assert extract("") == []


def test_extract_one_value_per_key() -> None:
    facts = [c for c in extract("叫咪咪，也叫小咪") if c.key == "pet_name"]
    assert len(facts) == 1


def test_decide_add_update_noop() -> None:
    assert decide(None, "牛奶").op is MemoryOp.ADD
    assert decide("牛奶", "牛奶").op is MemoryOp.NOOP
    assert decide("牛奶 ", "牛奶").op is MemoryOp.NOOP
    assert decide("牛奶", "牛肉").op is MemoryOp.UPDATE


@pytest.mark.asyncio
async def test_observe_adds_then_updates_then_noops() -> None:
    repo = InMemoryRepository()
    service = MemoryService(repo)

    added = await service.observe("1001", "5001", "它叫Lumina")
    assert [op for _fact, op in added] == [MemoryOp.ADD]

    repeated = await service.observe("1001", "5001", "它叫Lumina")
    assert repeated == [], "同一句话重复说不能产生新事实"

    updated = await service.observe("1001", "5001", "它改名叫小月亮了")
    assert [op for _fact, op in updated] == [MemoryOp.UPDATE]
    facts = await repo.list_memory_facts("1001", "5001")
    assert {f.key: f.value for f in facts}["pet_name"] == "小月亮"


@pytest.mark.asyncio
async def test_memory_is_isolated_by_pet_and_user() -> None:
    repo = InMemoryRepository()
    service = MemoryService(repo)
    await service.observe("1001", "5001", "它对牛奶过敏")
    await service.observe("1001", "5002", "它对花生过敏")
    await service.observe("1002", "5001", "它对鸡蛋过敏")

    assert [f.value for f in await repo.list_memory_facts("1001", "5001")] == ["牛奶"]
    assert [f.value for f in await repo.list_memory_facts("1001", "5002")] == ["花生"]
    assert [f.value for f in await repo.list_memory_facts("1002", "5001")] == ["鸡蛋"]


@pytest.mark.asyncio
async def test_recall_returns_labeled_lines_and_skips_low_confidence() -> None:
    repo = InMemoryRepository()
    await repo.upsert_memory_fact(
        MemoryFact(id="", user_id="1001", pet_id="5001", key="allergy", value="牛奶", confidence=0.95)
    )
    await repo.upsert_memory_fact(
        MemoryFact(id="", user_id="1001", pet_id="5001", key="food_like", value="冻干", confidence=0.3)
    )
    service = MemoryService(repo, min_confidence=0.7)

    lines = await service.recall_lines("1001", "5001")
    assert lines == ["过敏：牛奶"], "低置信度的猜测不能塞进系统提示"


def test_label_of_unknown_key_falls_back_to_key() -> None:
    assert label_of("allergy") == "过敏"
    assert label_of("mystery") == "mystery"


@pytest.mark.asyncio
async def test_upsert_keeps_first_created_time_and_id() -> None:
    repo = InMemoryRepository()
    first = await repo.upsert_memory_fact(
        MemoryFact(id="", user_id="1001", pet_id=None, key="pet_weight", value="4.6")
    )
    second = await repo.upsert_memory_fact(
        MemoryFact(id="", user_id="1001", pet_id=None, key="pet_weight", value="5.1")
    )
    assert second.id == first.id
    assert second.value == "5.1"
    facts = await repo.list_memory_facts("1001", None)
    assert len(facts) == 1
