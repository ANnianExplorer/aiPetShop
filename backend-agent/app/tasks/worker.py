"""任务消费者：按 topic 分发，失败退避重投，超限进死信。

一个 worker 一个循环，同一 topic 内串行（本项目旁路任务量小，
串行换取「同一用户的记忆不会被并发写乱」这个更值钱的保证）。

重试由巡检器统一驱动（B4）：
- `retry_due()` 把退避到期的消息搬回主队列；
- `sweep()` 回收卡在在途里的消息（消费者被杀）；
- 可选 `redrive_dead_letters()` 有界地自动重投死信（默认关闭）；
- `_check_dlq_alerts()` 在死信数越过阈值时告警（默认阈值 1，边沿触发）。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Mapping

from ..core.logging import log_event
from ..core.metrics import DLQ_ALERTS, metrics
from .base import TaskHandler, TaskMessage, TaskQueue

task_log = logging.getLogger("agent.task")


class TaskWorker:
    def __init__(
        self,
        queue: TaskQueue,
        handlers: Mapping[str, TaskHandler],
        *,
        topics: list[str] | None = None,
        idle_timeout_s: float = 1.0,
        sweep_interval_s: float = 0.0,
        visible_timeout_s: float = 120.0,
        dlq_redrive_interval_s: float = 0.0,
        dlq_max_redrives: int = 3,
        dlq_redrive_limit: int = 5,
        dlq_alert_threshold: int = 1,
    ) -> None:
        self._queue = queue
        self._handlers = dict(handlers)
        self._topics = topics or sorted(self._handlers)
        self._idle = idle_timeout_s
        self._sweep_interval = sweep_interval_s
        self._visible_timeout = visible_timeout_s
        self._dlq_redrive_interval = dlq_redrive_interval_s
        self._dlq_max_redrives = dlq_max_redrives
        self._dlq_redrive_limit = dlq_redrive_limit
        self._dlq_alert_threshold = dlq_alert_threshold
        # 已经报过警的 topic：边沿触发，持续超阈值不重复刷日志
        self._dlq_alert_active: set[str] = set()
        self._tasks: list[asyncio.Task[None]] = []
        self._stop = asyncio.Event()
        self.processed = 0
        self.failed = 0
        self.swept = 0
        self.promoted = 0
        self.redriven = 0

    async def _sweep_loop(self) -> None:
        """定期做四件事：搬回到期重试、回收在途、按需重投死信、检查死信阈值。"""
        if self._sweep_interval <= 0:
            return
        ticks = 0
        while not self._stop.is_set():
            try:
                await asyncio.sleep(self._sweep_interval)
                if self._stop.is_set():
                    return
                ticks += 1
                promoted = await self._queue.retry_due(self._topics)
                self.promoted += promoted
                moved = await self._queue.sweep(self._topics, older_than_s=self._visible_timeout)
                self.swept += moved
                if self._dlq_redrive_interval > 0:
                    every = max(1, int(self._dlq_redrive_interval / self._sweep_interval))
                    if ticks % every == 0:
                        redriven = await self._queue.redrive_dead_letters(
                            self._topics,
                            limit_per_topic=self._dlq_redrive_limit,
                            max_redrives=self._dlq_max_redrives,
                        )
                        self.redriven += redriven
                await self._check_dlq_alerts()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # 巡检本身不该把 worker 拖死
                log_event(task_log, logging.ERROR, "task sweep failed", error=f"{type(exc).__name__}: {exc}")
                await asyncio.sleep(1.0)

    async def _check_dlq_alerts(self) -> None:
        """死信数越过阈值时告警一次；回落后复位，下次再升上来会重新告警。

        只做「观察 + 打日志/计数」，不自动删除或重投死信——那是运维动作。
        阈值 0 表示关闭；巡检关闭时本方法不会被调用。
        """
        threshold = self._dlq_alert_threshold
        if threshold <= 0:
            return
        for topic in self._topics:
            count = await self._queue.dead_letter_count(topic)
            active = topic in self._dlq_alert_active
            if count >= threshold and not active:
                self._dlq_alert_active.add(topic)
                metrics.inc(DLQ_ALERTS, {"topic": topic})
                log_event(
                    task_log, logging.WARNING, "task dlq threshold exceeded",
                    topic=topic, dead_letters=count, threshold=threshold,
                )
            elif count < threshold and active:
                self._dlq_alert_active.discard(topic)
                log_event(
                    task_log, logging.INFO, "task dlq below threshold",
                    topic=topic, dead_letters=count, threshold=threshold,
                )

    async def _loop(self, topic: str) -> None:
        handler = self._handlers[topic]
        while not self._stop.is_set():
            try:
                message = await self._queue.receive(topic, timeout_s=self._idle)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # 中间件抖动不应该让 worker 退出
                log_event(task_log, logging.ERROR, "task receive failed", topic=topic, error=str(exc))
                await asyncio.sleep(1.0)
                continue
            if message is None:
                continue
            await self._handle(topic, message, handler)

    async def _handle(self, topic: str, message: TaskMessage, handler: TaskHandler) -> None:
        try:
            await handler(message)
        except asyncio.CancelledError:
            # 关闭中：不 ack，留给下次进程 recover_inflight
            raise
        except Exception as exc:
            self.failed += 1
            log_event(
                task_log, logging.WARNING, "task failed",
                topic=topic, key=message.key, attempt=message.attempt,
                error=f"{type(exc).__name__}: {exc}",
            )
            with contextlib.suppress(Exception):
                await self._queue.nack(message, error=f"{type(exc).__name__}: {exc}")
            return
        self.processed += 1
        with contextlib.suppress(Exception):
            await self._queue.ack(message)

    async def start(self) -> None:
        if self._tasks or not self._topics:
            return
        self._stop.clear()
        for topic in self._topics:
            self._tasks.append(asyncio.create_task(self._loop(topic), name=f"task-{topic}"))
        if self._sweep_interval > 0:
            self._tasks.append(asyncio.create_task(self._sweep_loop(), name="task-sweeper"))

    async def stop(self) -> None:
        self._stop.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        self._tasks.clear()

    async def drain(self, timeout_s: float = 3.0) -> None:
        """测试/退出前用：等队列空、没有待提升的重试，也没有新消息进来。"""
        deadline = asyncio.get_running_loop().time() + timeout_s
        while asyncio.get_running_loop().time() < deadline:
            await self._queue.retry_due(self._topics)
            pending = sum(await self._queue.depth(t) for t in self._topics)
            if pending == 0:
                return
            await asyncio.sleep(0.02)
