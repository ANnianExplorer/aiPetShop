"""旁路任务的消费者实现。

两个 topic、两条幂等规则：
- `agent.memory.observe`：记忆写入本身按 `(user, pet, key)` upsert，重复消费无害；
- `agent.audit.tool`：消息 id 直接当 `tool_call_log.id`，重复消费撞主键被忽略。
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from ..core.logging import log_event
from ..memory.service import MemoryService
from ..storage.base import AgentRepository
from .base import TaskHandler, TaskMessage

task_log = logging.getLogger("agent.task")


def _payload(message: TaskMessage) -> Mapping[str, object]:
    payload = message.payload
    if not isinstance(payload, Mapping):
        raise ValueError("任务载荷必须是对象")
    return payload


def build_handlers(
    memory: MemoryService,
    repository: AgentRepository,
) -> dict[str, TaskHandler]:
    async def observe_memory(message: TaskMessage) -> None:
        payload = _payload(message)
        user_id = str(payload.get("user_id") or "")
        text = str(payload.get("text") or "")
        if not user_id or not text:
            raise ValueError("memory.observe 缺少 user_id/text")
        pet_id = payload.get("pet_id")
        facts = await memory.observe(user_id, str(pet_id) if pet_id else None, text)
        log_event(task_log, logging.INFO, "task memory observed",
                  key=message.key, facts=len(facts))

    async def persist_audit(message: TaskMessage) -> None:
        payload = _payload(message)
        await repository.audit_tool_call(
            str(payload["run_id"]),
            str(payload["name"]),
            bool(payload["ok"]),
            payload.get("code") if payload.get("code") is None else str(payload["code"]),
            int(payload["latency_ms"]),
            str(payload["args_digest"]),
            event_id=message.id,
        )

    return {
        "agent.memory.observe": observe_memory,
        "agent.audit.tool": persist_audit,
    }
