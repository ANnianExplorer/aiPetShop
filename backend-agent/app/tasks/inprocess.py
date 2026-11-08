"""进程内实现：asyncio.Queue，单进程、重启即丢。

用途：开发环境与测试的默认实现。它证明业务代码不依赖中间件，
也保证「队列没配好」时系统仍然能跑（只是旁路工作变成同步）。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence

from ..core.logging import log_event
from .base import TaskMessage, TaskQueueFull, make_message

task_log = logging.getLogger("agent.task")


class InProcessTaskQueue:
    def __init__(self, *, topic: str, max_size: int = 1000, max_attempts: int = 3) -> None:
        self._queues: dict[str, asyncio.Queue[TaskMessage]] = {}
        self._dlq: dict[str, list[TaskMessage]] = {}
        self._max_size = max_size
        self._max_attempts = max_attempts

    def _queue(self, topic: str) -> asyncio.Queue[TaskMessage]:
        queue = self._queues.get(topic)
        if queue is None:
            queue = asyncio.Queue(maxsize=self._max_size)
            self._queues[topic] = queue
        return queue

    async def publish(self, topic: str, key: str, payload: Mapping[str, object]) -> str:
        message = make_message(topic, key, payload)
        try:
            self._queue(topic).put_nowait(message)
        except asyncio.QueueFull as exc:
            raise TaskQueueFull(f"任务队列已满（{self._max_size}）") from exc
        return message.id

    async def receive(self, topic: str, timeout_s: float = 1.0) -> TaskMessage | None:
        try:
            return await asyncio.wait_for(self._queue(topic).get(), timeout=timeout_s)
        except TimeoutError:
            return None
        except asyncio.QueueEmpty:  # 竞态兜底
            return None

    async def ack(self, message: TaskMessage) -> None:
        return None

    async def nack(self, message: TaskMessage, *, error: str) -> None:
        if message.attempt >= self._max_attempts:
            self._dlq.setdefault(message.topic, []).append(message)
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
        try:
            self._queue(message.topic).put_nowait(retried)
        except asyncio.QueueFull:
            self._dlq.setdefault(message.topic, []).append(retried)
            log_event(task_log, logging.ERROR, "task dead letter", topic=message.topic,
                      key=message.key, attempts=retried.attempt, error="queue full")

    async def depth(self, topic: str) -> int:
        return self._queue(topic).qsize()

    async def dead_letters(self, topic: str) -> list[TaskMessage]:
        """与 Redis 实现保持同一签名（异步），否则调用方要为两种后端写两套代码。"""
        return list(self._dlq.get(topic, ()))

    async def recover(self, topics: Sequence[str] | None = None) -> int:
        """内存队列没有「在途」状态：消息要么在队列里，要么已经被处理。"""
        return 0

    async def sweep(self, topics: Sequence[str], *, older_than_s: float) -> int:
        """内存队列的消费在同一进程内，没有跨进程「在途」状态可扫。"""
        return 0

    async def replay_dead_letter(self, topic: str, *, limit: int = 10) -> int:
        pending = self._dlq.get(topic, [])
        if limit <= 0 or not pending:
            return 0
        take = pending[:limit]
        del pending[: len(take)]
        replayed = 0
        for message in take:
            retried = TaskMessage(
                id=message.id,
                topic=message.topic,
                key=message.key,
                payload=message.payload,
                attempt=1,
            )
            try:
                self._queue(topic).put_nowait(retried)
            except asyncio.QueueFull:
                # 放不回去就留在死信里，不丢
                pending.append(message)
                break
            replayed += 1
        log_event(task_log, logging.INFO, "task dead letter replayed", topic=topic, replayed=replayed)
        return replayed

    async def aclose(self) -> None:
        self._queues.clear()
        self._dlq.clear()
