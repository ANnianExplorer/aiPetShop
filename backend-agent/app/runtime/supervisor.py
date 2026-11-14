"""把「一次运行」的生命周期从「一次 HTTP 连接」里拆出来。

为什么需要它：SSE 由请求协程直接驱动时，客户端一断线，生成器被关闭，运行的
`finally` 就把 run 标成 cancelled —— 事件日志里永远不会出现 `done`，所谓
"断线续传"只能续到半截。真实断网（切后台、进电梯、Wi-Fi 抖动）是常态，
所以运行必须有自己的宿主：请求走了，它照样跑完、照样把事件写进日志。

约定：
- 任务只增不减地登记在 `_tasks`，跑完自摘，避免 "Task was destroyed but it is pending"；
- 任务里的异常不能静默丢失（否则线上只会看到"永远没有 done"），一律落日志；
- `aclose()` 只在进程退出时调用：取消任务的瞬间，运行的 `finally` 会把它标成 cancelled，
  这比留下一个永远 `running` 的僵尸干净。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Coroutine
from typing import Any

from ..core.logging import log_event

supervisor_log = logging.getLogger("agent.supervisor")


class RunSupervisor:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    def spawn(self, coro: Coroutine[Any, Any, None], *, name: str) -> asyncio.Task[None]:
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._on_done)
        return task

    def _on_done(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            log_event(
                supervisor_log,
                logging.ERROR,
                "run task crashed",
                task=task.get_name(),
                error=f"{type(exc).__name__}: {exc}",
            )

    def running(self) -> int:
        return len(self._tasks)

    async def aclose(self) -> None:
        if not self._tasks:
            return
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        with contextlib.suppress(Exception):
            log_event(supervisor_log, logging.INFO, "supervisor closed", tasks=len(tasks))
