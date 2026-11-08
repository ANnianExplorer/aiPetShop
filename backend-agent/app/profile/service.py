"""画像服务：把「重算」这件事收在一处，接口与旁路任务共用。

三个约定：
1. **只重算不臆造**：数据源永远是 `memory_fact`，`build_profile` 决定长什么样；
2. **追加式版本**：每次重算写一版，旧版留给管理端 diff，只保留最近 N 版（默认 20）；
3. **重算失败不阻塞对话**：调用方（runner/consumer）必须吞异常，画像只是增强。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..core.ids import new_id
from ..domain.models import ProfileSnapshot
from ..storage.base import AgentRepository
from .builder import build_profile, profile_lines


@dataclass(frozen=True)
class ProfileView:
    snapshot: ProfileSnapshot
    stale: bool


class ProfileService:
    def __init__(
        self,
        repository: AgentRepository,
        *,
        keep_versions: int = 20,
        refresh_ttl_s: int = 300,
        vaccine_stale_days: int = 300,
        clock: Any = time.monotonic,
        ids: Any = None,
    ) -> None:
        self._repo = repository
        self._keep = max(1, int(keep_versions))
        self._ttl = max(0, int(refresh_ttl_s))
        self._vaccine_stale_days = max(1, int(vaccine_stale_days))
        self._clock = clock
        self._ids = ids or new_id
        # 去抖：同一个 (user, pet) 在 TTL 内不重复重算，避免每轮对话都写一版
        self._last_refresh: dict[tuple[str, str], float] = {}

    @staticmethod
    def _slot(user_id: str, pet_id: str | None) -> tuple[str, str]:
        return user_id, pet_id or ""

    def should_refresh(self, user_id: str, pet_id: str | None) -> bool:
        if self._ttl == 0:
            return True
        last = self._last_refresh.get(self._slot(user_id, pet_id))
        return last is None or (self._clock() - last) >= self._ttl

    async def rebuild(self, user_id: str, pet_id: str | None) -> ProfileSnapshot:
        facts = await self._repo.list_memory_facts(user_id, pet_id, limit=50)
        built = build_profile(facts, vaccine_stale_days=self._vaccine_stale_days)
        # 把「这次读到的最大事实时间」写进快照：之后只要有更新的事实就判过期，
        # 比拿快照时间戳比较更稳（同一秒内写入不会漏判）。
        watermark = max(
            (fact.update_time or fact.create_time or "" for fact in facts), default=""
        )
        data = dict(built["data"])
        data["meta"] = {"factWatermark": watermark, "builtAt": self.now_text()}
        version = await self._repo.next_profile_version(user_id, pet_id)
        snapshot = ProfileSnapshot(
            id=str(self._ids()),
            user_id=user_id,
            pet_id=pet_id,
            version=version,
            data=data,
            fact_count=int(built["fact_count"]),
            confidence=float(built["confidence"]),
        )
        saved = await self._repo.save_profile_snapshot(snapshot)
        await self._repo.prune_profile_versions(user_id, pet_id, self._keep)
        self._last_refresh[self._slot(user_id, pet_id)] = self._clock()
        return saved

    async def get(self, user_id: str, pet_id: str | None) -> ProfileView | None:
        snapshot = await self._repo.latest_profile_snapshot(user_id, pet_id)
        if snapshot is None:
            return None
        return ProfileView(snapshot=snapshot, stale=await self.is_stale(snapshot))

    async def is_stale(self, snapshot: ProfileSnapshot) -> bool:
        """事实比快照里的 watermark 新 → 过期。watermark 缺失时退回快照时间。"""
        latest_fact = await self._repo.latest_memory_update(snapshot.user_id, snapshot.pet_id)
        if not latest_fact:
            return False
        meta = snapshot.data.get("meta") if isinstance(snapshot.data, dict) else None
        watermark = ""
        if isinstance(meta, dict):
            watermark = str(meta.get("factWatermark") or "")
        return latest_fact > (watermark or snapshot.create_time or "")

    async def versions(
        self, user_id: str, pet_id: str | None, limit: int = 10
    ) -> list[ProfileSnapshot]:
        return await self._repo.list_profile_versions(user_id, pet_id, limit=limit)

    async def context_lines(self, user_id: str, pet_id: str | None) -> list[str]:
        """注入对话的短句：只放风险与待办，且容忍没有画像。"""
        snapshot = await self._repo.latest_profile_snapshot(user_id, pet_id)
        if snapshot is None:
            return []
        return profile_lines(snapshot.data, limit=2)

    @staticmethod
    def now_text() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
