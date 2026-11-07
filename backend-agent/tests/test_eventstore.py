"""事件存储：两份实现跑同一套契约，续传游标必须一致。"""

from __future__ import annotations

import json

import pytest

from app.domain.events import Event, EventType
from app.runtime.eventlog import MemoryEventStore, RedisEventStore


class FakeRedisStreams:
    """只实现事件存储用到的命令；pipeline 不需要，这里直接串行调用。"""

    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.streams: dict[str, list[tuple[str, dict]]] = {}
        self.expires: dict[str, int] = {}
        self._entry = 0

    async def incr(self, key: str) -> int:
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    async def get(self, key: str) -> str | None:
        value = self.values.get(key)
        return str(value) if value is not None else None

    async def expire(self, key: str, ttl: int) -> bool:
        self.expires[key] = int(ttl)
        return True

    async def xadd(self, key: str, fields: dict, *, maxlen: int | None = None, approximate: bool = False) -> str:
        self._entry += 1
        entry_id = f"{self._entry}-0"
        bucket = self.streams.setdefault(key, [])
        bucket.append((entry_id, dict(fields)))
        if maxlen is not None and len(bucket) > maxlen:
            del bucket[: len(bucket) - maxlen]
        return entry_id

    async def xrange(self, key: str, min: str = "-", max: str = "+") -> list[tuple[str, dict]]:
        return list(self.streams.get(key, []))


def _event(kind: EventType, **data) -> Event:
    return Event(kind, data)


@pytest.mark.asyncio
async def test_memory_store_assigns_sequential_seq() -> None:
    store = MemoryEventStore()
    first = await store.append("run-1", _event(EventType.ROUTE, session_id="s1"))
    second = await store.append("run-1", _event(EventType.DELTA, text="你"))
    third = await store.append("run-1", _event(EventType.DONE, answer="你好"))
    assert [first.seq, second.seq, third.seq] == [1, 2, 3]
    assert await store.last_seq("run-1") == 3
    await store.aclose()


@pytest.mark.asyncio
async def test_memory_store_replay_after_cursor() -> None:
    store = MemoryEventStore()
    for index in range(5):
        await store.append("run-1", _event(EventType.DELTA, text=str(index)))

    assert [e.seq for e in await store.events("run-1")] == [1, 2, 3, 4, 5]
    assert [e.seq for e in await store.events("run-1", 3)] == [4, 5]
    assert await store.events("missing", 0) == []
    await store.aclose()


@pytest.mark.asyncio
async def test_memory_store_trims_to_capacity() -> None:
    store = MemoryEventStore(capacity=4)
    for index in range(6):
        await store.append("run-1", _event(EventType.DELTA, text=str(index)))
    events = await store.events("run-1")
    assert [e.seq for e in events] == [3, 4, 5, 6], "只保留尾部，但序号不回退"
    await store.aclose()


@pytest.mark.asyncio
async def test_runs_do_not_share_seq() -> None:
    store = MemoryEventStore()
    await store.append("a", _event(EventType.ROUTE))
    await store.append("a", _event(EventType.DONE))
    first_b = await store.append("b", _event(EventType.ROUTE))
    assert first_b.seq == 1
    await store.aclose()


@pytest.mark.asyncio
async def test_redis_store_roundtrip_preserves_payload() -> None:
    client = FakeRedisStreams()
    store = RedisEventStore(client, capacity=10, ttl_s=600)
    event = _event(EventType.TOOL, name="search_logs", status="ok", latency_ms=12)
    stored = await store.append("run-9", event)

    assert stored.seq == 1
    assert client.expires["agent:events:run-9"] == 600
    assert client.expires["agent:events:run-9:seq"] == 600

    rows = await store.events("run-9")
    assert len(rows) == 1
    assert rows[0].type is EventType.TOOL
    assert rows[0].data["name"] == "search_logs"
    assert json.loads(client.streams["agent:events:run-9"][0][1]["payload"])["seq"] == 1


@pytest.mark.asyncio
async def test_redis_store_after_cursor_and_last_seq() -> None:
    client = FakeRedisStreams()
    store = RedisEventStore(client, capacity=50, ttl_s=600)
    for index in range(3):
        await store.append("r", _event(EventType.DELTA, text=str(index)))

    assert await store.last_seq("r") == 3
    assert [e.seq for e in await store.events("r", 1)] == [2, 3]
    assert await store.last_seq("unknown") == 0


@pytest.mark.asyncio
async def test_redis_store_skips_corrupt_payload() -> None:
    client = FakeRedisStreams()
    store = RedisEventStore(client, capacity=10, ttl_s=600)
    await store.append("r", _event(EventType.DELTA, text="ok"))
    client.streams["agent:events:r"].append(("99-0", {"seq": "9", "payload": "{not json"}))

    events = await store.events("r")
    assert [e.seq for e in events] == [1], "坏数据跳过而不是让整次续传 500"
