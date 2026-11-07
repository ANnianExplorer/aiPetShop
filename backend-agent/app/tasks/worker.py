"""任务消费者：按 topic 分发，失败重投，超限进死信。

一个 worker 一个循环，同一 topic 内串行（本项目旁路任务量小，
串行换取「同一用户的记忆不会被并发写乱」这个更值钱的保证）。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Mapping

from ..core.logging import log_event
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
    ) -> None:
        self._queue = queue
        self._handlers = dict(handlers)
        self._topics = topics or sorted(self._handlers)
        self._idle = idle_timeout_s
        self._tasks: list[asyncio.Task[None]] = []
        self._stop = asyncio.Event()
        self.processed = 0
        self.failed = 0

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

    async def stop(self) -> None:
        self._stop.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        self._tasks.clear()

    async def drain(self, timeout_s: float = 3.0) -> None:
        """测试/退出前用：等队列空且没有新消息进来。"""
        deadline = asyncio.get_running_loop().time() + timeout_s
        while asyncio.get_running_loop().time() < deadline:
            pending = sum(await self._queue.depth(t) for t in self._topics)
            if pending == 0:
                return
            await asyncio.sleep(0.02)
