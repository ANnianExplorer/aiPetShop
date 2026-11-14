"""跟随一次运行的事件流：从游标 `after` 读到终止事件为止。

和"读一次快照"的区别只有一个字：**等到**。断线重连要的不是"此刻之前发生了什么"，
而是"我走之后又发生了什么，直到这一轮真正结束"。两者读的是同一份事件日志，
所以多副本下（A 实例写的、B 实例收的重连）也能续上。

三条停止条件，缺一不可：
1. 读到 `done` / `error`：本轮真的结束了；
2. 日志再没有新事件，且库里 run 已不在 `running`：日志可能被 TTL 清掉，
   此时不能指望 `done` 还活着，必须靠库状态收口，否则客户端永远转圈；
3. 跟随超时：运行还在跑但已经超过 `idle_timeout_s`，先返回，让客户端再连一次
   （长连接在网关那侧也未必撑得住，主动断比被中间层掐死可诊断）。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

from ..domain.events import Event, EventType
from ..domain.models import RunStatus
from ..storage.base import AgentRepository
from .eventlog import EventStore

TERMINAL = frozenset({EventType.DONE, EventType.ERROR})


async def follow_events(
    log: EventStore,
    repo: AgentRepository,
    run_id: str,
    after: int = 0,
    *,
    poll_s: float = 0.05,
    idle_timeout_s: float = 90.0,
) -> AsyncIterator[Event]:
    cursor = max(after, 0)
    deadline = time.monotonic() + idle_timeout_s
    while True:
        events = await log.events(run_id, cursor)
        for event in events:
            if event.seq <= cursor:  # 存储实现不该回重复，防御一下：顺序是契约
                continue
            cursor = event.seq
            yield event
            if event.type in TERMINAL:
                return

        run = await repo.get_run(run_id)
        if run is None:
            return
        if run.status is not RunStatus.RUNNING:
            # 状态已终态但日志里没有终止事件：要么被裁剪，要么写入与状态更新有毫秒级交错。
            # 再读一次确认真的没有新东西，才收口。
            tail = await log.events(run_id, cursor)
            if not tail:
                return
            continue

        if time.monotonic() >= deadline:
            return
        await asyncio.sleep(poll_s)
