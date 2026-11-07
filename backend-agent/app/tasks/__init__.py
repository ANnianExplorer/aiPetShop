"""任务队列装配：按配置选实现，业务侧只认 `TaskQueue` 协议。"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..core.logging import log_event
from ..core.redis_client import create_redis
from .base import TaskHandler, TaskMessage, TaskQueue, TaskQueueFull
from .inprocess import InProcessTaskQueue
from .redis_queue import RedisTaskQueue
from .worker import TaskWorker

if TYPE_CHECKING:  # pragma: no cover
    from ..config import Settings

task_log = logging.getLogger("agent.task")

TOPIC_MEMORY_OBSERVE = "agent.memory.observe"
TOPIC_AUDIT_TOOL = "agent.audit.tool"
TOPICS = (TOPIC_MEMORY_OBSERVE, TOPIC_AUDIT_TOOL)

__all__ = [
    "TOPICS",
    "TOPIC_AUDIT_TOOL",
    "TOPIC_MEMORY_OBSERVE",
    "InProcessTaskQueue",
    "RedisTaskQueue",
    "TaskHandler",
    "TaskMessage",
    "TaskQueue",
    "TaskQueueFull",
    "TaskWorker",
    "create_task_queue",
]


def create_task_queue(settings: Settings) -> TaskQueue | None:
    """`off` 返回 None（调用方降级为同步执行）；实现异常时不阻断启动。"""
    backend = settings.task_backend
    if backend == "off":
        return None
    if backend == "memory":
        return InProcessTaskQueue(
            topic=TOPIC_MEMORY_OBSERVE,
            max_size=settings.task_queue_size,
            max_attempts=settings.task_max_attempts,
        )
    try:
        client = create_redis(settings.redis_url)
        return RedisTaskQueue(client, max_attempts=settings.task_max_attempts)
    except Exception as exc:  # 连不上 Redis 也不该让服务起不来
        log_event(task_log, logging.ERROR, "task queue init failed",
                  backend=backend, error=f"{type(exc).__name__}: {exc}")
        return None
