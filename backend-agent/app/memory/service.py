"""记忆服务：抽取 → 决策 → 落库；召回 → 拼成给模型的上下文行。

边界（写进 SPEC，测试盯着）：
1. 记忆只属于 `(user_id, pet_id)`：换宠物不串味，多用户之间物理隔离；
2. 写入幂等：同一句话重复说，第二次是 NOOP，不会产生重复行；
3. 召回只读已确认的事实（confidence ≥ 阈值），不把"猜测"塞进系统提示；
4. 记忆写入失败绝不能影响对话本身——调用方必须容错，这里也吞掉异常只记日志；
5. 情景记忆只抢救「发生过的事」，一条消息最多一条，按来源消息 id 幂等。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..core.logging import log_event
from ..domain.models import MemoryEpisode, MemoryFact
from .episodes import extract_episode, format_episode_line, select_episodes
from .extract import extract, label_of
from .ops import MemoryOp, decide

memory_log = logging.getLogger("agent.memory")


class MemoryService:
    def __init__(self, repo: Any, *, min_confidence: float = 0.7) -> None:
        self._repo = repo
        self._min_confidence = min_confidence

    async def observe(
        self, user_id: str, pet_id: str | None, text: str
    ) -> list[tuple[MemoryFact, MemoryOp]]:
        """从用户这句话里学习事实。返回写入成功的 (fact, op)，便于测试与审计。"""
        written: list[tuple[MemoryFact, MemoryOp]] = []
        for cand in extract(text):
            if cand.confidence < self._min_confidence:
                continue
            existing = await self._repo.get_memory_fact(user_id, pet_id, cand.key)
            decision = decide(existing.value if existing else None, cand.value)
            if decision.op is MemoryOp.NOOP:
                continue
            fact = MemoryFact(
                id=existing.id if existing else "",
                user_id=user_id,
                pet_id=pet_id,
                key=cand.key,
                value=cand.value,
                confidence=max(cand.confidence, existing.confidence if existing else 0.0),
                source="conversation",
            )
            saved = await self._repo.upsert_memory_fact(fact)
            written.append((saved, decision.op))
            log_event(
                memory_log,
                logging.INFO,
                "memory written",
                key=cand.key,
                op=decision.op.value,
                confidence=round(fact.confidence, 2),
            )
        return written

    async def recall_lines(self, user_id: str, pet_id: str | None, limit: int = 6) -> list[str]:
        """召回的形态是「标签：值」而不是 JSON——模型读起来更稳，也更省 token。"""
        facts = await self._repo.list_memory_facts(user_id, pet_id, limit)
        return [f"{label_of(f.key)}：{f.value}" for f in facts if f.confidence >= self._min_confidence]

    async def record_episode(
        self,
        user_id: str,
        pet_id: str | None,
        text: str,
        *,
        session_id: str | None = None,
        message_id: str | None = None,
        run_id: str | None = None,
        now: datetime | None = None,
    ) -> MemoryEpisode | None:
        """把这句话里的「已发生事件」写成情景；没有可记的返回 None。"""
        candidate = extract_episode(text, now=now)
        if candidate is None:
            return None
        episode = MemoryEpisode(
            id="",
            user_id=user_id,
            pet_id=pet_id,
            session_id=session_id,
            source_message_id=message_id,
            kind=candidate.kind,
            summary=candidate.summary,
            occurred_at=candidate.occurred_at,
            detail={"time_word": candidate.time_word, "run_id": run_id, "source": "conversation"},
        )
        saved = await self._repo.add_memory_episode(episode)
        log_event(
            memory_log,
            logging.INFO,
            "memory episode written",
            episode_id=saved.id,
            kind=saved.kind,
            occurred_at=saved.occurred_at,
        )
        return saved

    async def episode_lines(
        self,
        user_id: str,
        pet_id: str | None,
        question: str,
        limit: int = 3,
        *,
        now: datetime | None = None,
    ) -> list[str]:
        """召回与当前问题相关的往事；没有命中返回空列表。"""
        episodes = await self._repo.list_memory_episodes(user_id, pet_id, 200)
        picked = select_episodes(question, episodes, limit=limit, now=now)
        return [format_episode_line(episode) for episode in picked]
