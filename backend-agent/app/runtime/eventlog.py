"""每次运行的事件日志：断线重连的续传依据。

两种实现语义一致（同一套契约测试跑两遍）：
- `MemoryEventStore`：单进程，零依赖，dev/test 默认；
- `RedisEventStore`：多副本部署（A 收到请求、B 收到重连也能续传），Stream + 序号键。

为什么序号自己分配而不是用 Stream 的 entry id：`Last-Event-ID` 是给客户端用的整数游标，
用 `INCR` 分配比解析 `1700000000000-0` 稳定，也不受 `XADD` 时钟回拨影响。

进程重启 + 内存后端的后果：续传丢失，但完整轨迹已经在 `agent_step` / `agent_message` 里，
管理端回放不受影响——这是 ADR-0003 写明的降级路径。
"""

from __future__ import annotations

import contextlib
import json
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from ..domain.events import Event


class EventStore(Protocol):
    async def append(self, run_id: str, event: Event) -> Event: ...

    async def events(self, run_id: str, after_seq: int = 0) -> list[Event]: ...

    async def last_seq(self, run_id: str) -> int: ...

    async def aclose(self) -> None: ...


_PRUNE_EVERY = 64


@dataclass
class _Entry:
    events: list[Event]
    touched: float


class MemoryEventStore:
    def __init__(self, capacity: int = 512, ttl_s: float = 900.0) -> None:
        self._capacity = capacity
        self._ttl = ttl_s
        self._runs: dict[str, _Entry] = {}
        self._writes = 0

    async def append(self, run_id: str, event: Event) -> Event:
        entry = self._runs.get(run_id)
        if entry is None:
            entry = _Entry(events=[], touched=time.monotonic())
            self._runs[run_id] = entry
        seq = (entry.events[-1].seq + 1) if entry.events else 1
        stored = event.with_seq(seq)
        entry.events.append(stored)
        entry.touched = time.monotonic()
        if len(entry.events) > self._capacity:
            # 只保留尾部：长时间任务也只回放最近一段
            del entry.events[: len(entry.events) - self._capacity]
        self._writes += 1
        if self._writes % _PRUNE_EVERY == 0:
            self._prune()
        return stored

    async def events(self, run_id: str, after_seq: int = 0) -> list[Event]:
        entry = self._runs.get(run_id)
        if entry is None:
            return []
        return [e for e in entry.events if e.seq > after_seq]

    async def last_seq(self, run_id: str) -> int:
        entry = self._runs.get(run_id)
        return entry.events[-1].seq if entry and entry.events else 0

    async def replay(self, run_id: str, after_seq: int = 0) -> Iterable[Event]:
        return iter(await self.events(run_id, after_seq))

    async def aclose(self) -> None:
        self._runs.clear()

    def _prune(self) -> None:
        deadline = time.monotonic() - self._ttl
        stale = [rid for rid, entry in self._runs.items() if entry.touched < deadline]
        for rid in stale:
            self._runs.pop(rid, None)


class RedisEventStore:
    """Stream 存事件、`INCR` 存序号；两者共用同一个 TTL，run 结束后自然消失。"""

    def __init__(self, client: Any, *, capacity: int = 512, ttl_s: float = 900.0) -> None:
        self._client = client
        self._capacity = capacity
        self._ttl = int(ttl_s)

    @staticmethod
    def _key(run_id: str) -> str:
        return f"agent:events:{run_id}"

    @staticmethod
    def _seq_key(run_id: str) -> str:
        return f"agent:events:{run_id}:seq"

    async def append(self, run_id: str, event: Event) -> Event:
        seq = int(await self._client.incr(self._seq_key(run_id)))
        stored = event.with_seq(seq)
        await self._client.xadd(
            self._key(run_id),
            {"seq": seq, "payload": json.dumps(stored.to_payload(), ensure_ascii=False)},
            maxlen=self._capacity,
            approximate=False,
        )
        await self._client.expire(self._seq_key(run_id), self._ttl)
        await self._client.expire(self._key(run_id), self._ttl)
        return stored

    async def events(self, run_id: str, after_seq: int = 0) -> list[Event]:
        rows = await self._client.xrange(self._key(run_id), min="-", max="+")
        out: list[Event] = []
        for _entry_id, fields in rows:
            seq = int(_field(fields, "seq") or 0)
            if seq <= after_seq:
                continue
            raw = _field(fields, "payload")
            if not raw:
                continue
            try:
                out.append(Event.from_payload(json.loads(raw)))
            except (TypeError, ValueError):
                continue
        out.sort(key=lambda e: e.seq)
        return out

    async def last_seq(self, run_id: str) -> int:
        raw = await self._client.get(self._seq_key(run_id))
        return int(raw or 0)

    async def aclose(self) -> None:
        closer = getattr(self._client, "aclose", None) or getattr(self._client, "close", None)
        if closer is not None:
            with contextlib.suppress(Exception):
                await closer()


def _field(fields: Any, name: str) -> str | None:
    if isinstance(fields, dict):
        value = fields.get(name)
    else:  # redis-py 在 decode_responses=False 时返回 [k, v, k, v]
        value = None
        pairs = list(fields or [])
        for index in range(0, len(pairs) - 1, 2):
            if pairs[index] == name:
                value = pairs[index + 1]
                break
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else str(value)


def create_event_store(settings: Any) -> EventStore:
    if settings.event_backend == "redis":
        from redis.asyncio import from_url

        client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        return RedisEventStore(
            client,
            capacity=settings.event_log_capacity,
            ttl_s=settings.event_log_ttl_s,
        )
    return MemoryEventStore(settings.event_log_capacity, settings.event_log_ttl_s)


# 兼容旧名字：S1.5 的代码/文档里叫 RunEventLog
RunEventLog = MemoryEventStore
