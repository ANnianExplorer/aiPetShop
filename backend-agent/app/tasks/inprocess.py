"""进程内实现：asyncio.Queue，单进程、重启即丢。

用途：开发环境与测试的默认实现。它证明业务代码不依赖中间件，
也保证「队列没配好」时系统仍然能跑（只是旁路工作变成同步）。

重试语义与 Redis 实现对齐：失败先进 `:retry`（带退避到期时间），
巡检器调用 `retry_due()` 才搬回主队列——这样两套实现的行为可以被同一批测试钉住。
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Mapping, Sequence

from ..core.logging import log_event
from .base import TaskMessage, TaskQueueFull, backoff_seconds, make_message

task_log = logging.getLogger("agent.task")


class InProcessTaskQueue:
    def __init__(
        self,
        *,
        topic: str,
        max_size: int = 1000,
        max_attempts: int = 3,
        retry_base_s: float = 5.0,
        retry_cap_s: float = 600.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._queues: dict[str, asyncio.Queue[TaskMessage]] = {}
        self._dlq: dict[str, list[TaskMessage]] = {}
        # (到期时刻, 消息)；巡检时把到期的搬回主队列
        self._retry: dict[str, list[tuple[float, TaskMessage]]] = {}
        self._max_size = max_size
        self._max_attempts = max_attempts
        self._retry_base = retry_base_s
        self._retry_cap = retry_cap_s
        self._clock = clock or time.time

    def _queue(self, topic: str) -> asyncio.Queue[TaskMessage]:
        queue = self._queues.get(topic)
        if queue is None:
            queue = asyncio.Queue(maxsize=self._max_size)
            self._queues[topic] = queue
        return queue

    def _schedule_retry(self, message: TaskMessage) -> bool:
        """写入退避队列；返回是否成功（队列满/无退避时为 False 交给调用方兜底）。"""
        delay = backoff_seconds(message.attempt, base=self._retry_base, cap=self._retry_cap)
        self._retry.setdefault(message.topic, []).append((self._clock() + delay, message))
        return True

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
        retried = message.reborn(attempt=message.attempt + 1)
        try:
            self._schedule_retry(retried)
        except Exception:  # 退避登记失败时退回立即重试，任务不能丢
            self._queue(message.topic).put_nowait(retried)
        log_event(task_log, logging.WARNING, "task retry scheduled", topic=message.topic,
                  key=message.key, attempt=retried.attempt, error=error)

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

    async def retry_due(
        self, topics: Sequence[str], *, now: float | None = None
    ) -> int:
        deadline = self._clock() if now is None else float(now)
        moved = 0
        for topic in topics:
            pending = self._retry.get(topic) or []
            if not pending:
                continue
            keep: list[tuple[float, TaskMessage]] = []
            for due, message in pending:
                if due > deadline:
                    keep.append((due, message))
                    continue
                try:
                    self._queue(topic).put_nowait(message)
                except asyncio.QueueFull:
                    keep.append((due, message))  # 放不下就继续等，不丢
                    continue
                moved += 1
            self._retry[topic] = keep
        if moved:
            log_event(task_log, logging.INFO, "task retry promoted", moved=moved)
        return moved

    async def redrive_dead_letters(
        self, topics: Sequence[str], *, limit_per_topic: int, max_redrives: int
    ) -> int:
        if limit_per_topic <= 0 or max_redrives <= 0:
            return 0
        moved = 0
        for topic in topics:
            pending = self._dlq.get(topic) or []
            if not pending:
                continue
            keep: list[TaskMessage] = []
            taken = 0
            for message in pending:
                if taken >= limit_per_topic or message.redrives >= max_redrives:
                    keep.append(message)
                    continue
                retried = message.reborn(attempt=1, redrives=message.redrives + 1)
                try:
                    self._queue(topic).put_nowait(retried)
                except asyncio.QueueFull:
                    keep.append(message)
                    continue
                taken += 1
                moved += 1
            self._dlq[topic] = keep
        if moved:
            log_event(task_log, logging.WARNING, "task dead letters redriven", moved=moved)
        return moved

    async def replay_dead_letter(self, topic: str, *, limit: int = 10) -> int:
        pending = self._dlq.get(topic, [])
        if limit <= 0 or not pending:
            return 0
        take = pending[:limit]
        del pending[: len(take)]
        replayed = 0
        for message in take:
            retried = message.reborn(attempt=1)
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
        self._retry.clear()
