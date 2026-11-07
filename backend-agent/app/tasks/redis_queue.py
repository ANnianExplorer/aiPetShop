"""Redis 列表实现：`LPUSH` 投递 + `BRPOPLPUSH` 取用 + processing 列表保底。

只用了 Redis 5.0 就有的命令（`LPUSH` / `RPOPLPUSH` / `LREM` / `LLEN` / `LRANGE`），
**没有**用 Stream consumer group——那套语义本项目只需要一进一出，
列表够用，而且测试里能用一个极小的 FakeRedis 覆盖。

崩溃语义（at-least-once）：消息取走后放进 `:processing`，ack 才删。
进程崩了，下一次消费把 processing 里的残留搬回主列表（`recover_inflight`），
代价是可能重复投递一次——消费端按 key 幂等，见 ADR-0009 第 4 条。
"""

from __future__ import annotations

import contextlib
import json
import logging
from collections.abc import Awaitable, Mapping
from typing import Any, Protocol

from ..core.logging import log_event
from .base import TaskMessage, TaskQueueFull, make_message

task_log = logging.getLogger("agent.task")

_DLQ_SUFFIX = ":dlq"
_PROCESSING_SUFFIX = ":processing"


class RedisLike(Protocol):
    """只声明用到的命令，方便测试注入 FakeRedis。"""

    async def lpush(self, key: str, *values: str) -> int: ...
    async def rpoplpush(self, src: str, dst: str) -> str | None: ...
    async def brpoplpush(self, src: str, dst: str, timeout: int) -> str | None: ...
    async def lrem(self, key: str, count: int, value: str) -> int: ...
    async def llen(self, key: str) -> int: ...
    async def lrange(self, key: str, start: int, end: int) -> list[str]: ...
    async def aclose(self) -> None: ...


class RedisTaskQueue:
    def __init__(
        self,
        client: RedisLike,
        *,
        prefix: str = "pet:task",
        max_attempts: int = 3,
        block_timeout_s: int = 1,
    ) -> None:
        self._redis = client
        self._prefix = prefix
        self._max_attempts = max_attempts
        self._block_timeout = max(1, int(block_timeout_s))

    # ------------------------------------------------------------------ key
    def _topic_key(self, topic: str) -> str:
        return f"{self._prefix}:{topic}"

    def _processing_key(self, topic: str) -> str:
        return f"{self._topic_key(topic)}{_PROCESSING_SUFFIX}"

    def _dlq_key(self, topic: str) -> str:
        return f"{self._topic_key(topic)}{_DLQ_SUFFIX}"

    # -------------------------------------------------------------- publish
    async def publish(self, topic: str, key: str, payload: Mapping[str, Any]) -> str:
        message = make_message(topic, key, payload)
        try:
            await self._redis.lpush(self._topic_key(topic), json.dumps(message.to_json(), ensure_ascii=False))
        except Exception as exc:  # 中间件故障：让调用方降级为同步执行
            raise TaskQueueFull(f"Redis 任务队列不可用：{exc}") from exc
        return message.id

    # -------------------------------------------------------------- consume
    async def receive(self, topic: str, timeout_s: float = 1.0) -> TaskMessage | None:
        raw = await self._redis.brpoplpush(
            self._topic_key(topic), self._processing_key(topic), self._block_timeout
        )
        if raw is None:
            return None
        try:
            return TaskMessage.from_json(json.loads(raw))
        except (ValueError, KeyError, TypeError) as exc:
            # 坏消息不能卡住队列：直接进死信并返回 None
            await self._redis.lpush(self._dlq_key(topic), raw)
            log_event(task_log, logging.ERROR, "task payload invalid", topic=topic, error=str(exc))
            return None

    async def ack(self, message: TaskMessage) -> None:
        raw = json.dumps(message.to_json(), ensure_ascii=False)
        await self._redis.lrem(self._processing_key(message.topic), 1, raw)

    async def nack(self, message: TaskMessage, *, error: str) -> None:
        raw = json.dumps(message.to_json(), ensure_ascii=False)
        await self._redis.lrem(self._processing_key(message.topic), 1, raw)
        if message.attempt >= self._max_attempts:
            await self._redis.lpush(self._dlq_key(message.topic), raw)
            log_event(task_log, logging.ERROR, "task dead letter", topic=message.topic,
                      key=message.key, attempts=message.attempt, error=error)
            return
        retried = TaskMessage(
            id=message.id,
            topic=message.topic,
            key=message.key,
            payload=message.payload,
            attempt=message.attempt + 1,
        )
        await self._redis.lpush(
            self._topic_key(message.topic), json.dumps(retried.to_json(), ensure_ascii=False)
        )

    async def depth(self, topic: str) -> int:
        return int(await self._redis.llen(self._topic_key(topic)))

    async def dead_letters(self, topic: str) -> list[TaskMessage]:
        raws = await self._redis.lrange(self._dlq_key(topic), 0, -1)
        out: list[TaskMessage] = []
        for raw in raws:
            with contextlib.suppress(ValueError, KeyError, TypeError):
                out.append(TaskMessage.from_json(json.loads(raw)))
        return out

    async def recover_inflight(self, topic: str) -> int:
        """把 processing 里残留的消息搬回主列表（进程崩溃后的补偿）。返回条数。"""
        moved = 0
        while True:
            raw = await self._redis.rpoplpush(
                self._processing_key(topic), self._topic_key(topic)
            )
            if raw is None:
                break
            moved += 1
        if moved:
            log_event(task_log, logging.WARNING, "task inflight recovered", topic=topic, moved=moved)
        return moved

    async def aclose(self) -> None:
        closer: Awaitable[None] | None = getattr(self._redis, "aclose", None)
        if closer is not None:
            await closer()
