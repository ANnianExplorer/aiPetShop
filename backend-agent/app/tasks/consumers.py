"""旁路任务的消费者实现。

四个 topic、四条幂等规则：
- `agent.memory.observe`：记忆写入本身按 `(user, pet, key)` upsert，重复消费无害；
- `agent.audit.tool`：消息 id 直接当 `tool_call_log.id`，重复消费撞主键被忽略；
- `agent.doc.ingest`：文档状态机幂等（ready 的文档重复消费直接跳过）；
- `agent.profile.refresh`：重算得到的是「事实的当前快照」，重复消费只会多一个版本。
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from ..core.logging import log_event
from ..memory.service import MemoryService
from ..profile.service import ProfileService
from ..rag.models import DocumentStatus
from ..rag.service import DocumentService
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
    docs: DocumentService | None = None,
    profiles: ProfileService | None = None,
) -> dict[str, TaskHandler]:
    async def observe_memory(message: TaskMessage) -> None:
        payload = _payload(message)
        user_id = str(payload.get("user_id") or "")
        text = str(payload.get("text") or "")
        if not user_id or not text:
            raise ValueError("memory.observe 缺少 user_id/text")
        pet_id = payload.get("pet_id")
        slot = str(pet_id) if pet_id else None
        facts = await memory.observe(user_id, slot, text)
        log_event(task_log, logging.INFO, "task memory observed",
                  key=message.key, facts=len(facts))
        # 画像必须在事实写完之后重算：放在同一个消费者里，因果顺序天然成立；
        # 去抖交给 ProfileService（默认 5 分钟内不重复写版本）。
        if profiles is not None and profiles.should_refresh(user_id, slot):
            snapshot = await profiles.rebuild(user_id, slot)
            log_event(task_log, logging.INFO, "task profile rebuilt",
                      key=message.key, version=snapshot.version, facts=snapshot.fact_count)

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

    async def ingest_document(message: TaskMessage) -> None:
        if docs is None:
            raise ValueError("文档服务未装配，无法消费 agent.doc.ingest")
        payload = _payload(message)
        user_id = str(payload.get("user_id") or "")
        document_id = str(payload.get("document_id") or "")
        if not user_id or not document_id:
            raise ValueError("doc.ingest 缺少 user_id/document_id")
        document = await repository.get_document(user_id, document_id)
        if document is None:
            log_event(task_log, logging.WARNING, "task doc missing", document=document_id)
            return
        if document.status is DocumentStatus.READY:
            log_event(task_log, logging.INFO, "task doc skipped", document=document_id)
            return
        result = await docs.process(document)
        log_event(
            task_log,
            logging.INFO,
            "task doc ingested",
            document=document_id,
            status=int(result.status),
            chunks=result.chunk_count,
        )

    handlers: dict[str, TaskHandler] = {
        "agent.memory.observe": observe_memory,
        "agent.audit.tool": persist_audit,
    }
    if docs is not None:
        handlers["agent.doc.ingest"] = ingest_document
    return handlers
