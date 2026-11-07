"""每次运行的事件日志：断线重连的续传依据。

为什么不用数据库：SSE 续传是秒级行为，Redis/MySQL 只增加写放大；
事件序号由本日志分配，`GET /agent/runs/{run_id}/events` 按 `Last-Event-ID` 回放。
进程重启后无法续传 —— 但完整轨迹已经在 `agent_step` / `agent_message` 里，管理端回放不受影响。
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass

from ..domain.events import Event

_PRUNE_EVERY = 64


@dataclass
class _Entry:
    events: list[Event]
    touched: float


class RunEventLog:
    def __init__(self, capacity: int = 512, ttl_s: float = 900.0) -> None:
        self._capacity = capacity
        self._ttl = ttl_s
        self._runs: dict[str, _Entry] = {}
        self._writes = 0

    def append(self, run_id: str, event: Event) -> Event:
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

    def events(self, run_id: str, after_seq: int = 0) -> list[Event]:
        entry = self._runs.get(run_id)
        if entry is None:
            return []
        return [e for e in entry.events if e.seq > after_seq]

    def last_seq(self, run_id: str) -> int:
        entry = self._runs.get(run_id)
        return entry.events[-1].seq if entry and entry.events else 0

    def contains(self, run_id: str) -> bool:
        return run_id in self._runs

    def replay(self, run_id: str, after_seq: int = 0) -> Iterable[Event]:
        return iter(self.events(run_id, after_seq))

    def _prune(self) -> None:
        deadline = time.monotonic() - self._ttl
        stale = [rid for rid, entry in self._runs.items() if entry.touched < deadline]
        for rid in stale:
            self._runs.pop(rid, None)
