"""运行巡检：把「进程没了、run 还停在 running」的脏数据收敛成终态。

为什么需要它：`AgentRunner` 的 `finally` 能兜住正常结束、异常和客户端断开，但兜不住
**进程直接消失**（`kill -9`、OOM、机器重启）。这种 run 会永远停在 `running`，
管理端看起来像「任务卡住了」，前端重连也永远等不到 `done`。

策略：
- 只看**开始时间**超过 `stale_run_timeout_s` 的 run。运行本身受 `run_deadline_s` 兜底，
  超时还在跑只能是进程没了；
- 收敛成 `cancelled` 并写入人话原因（管理端 `AdminRunOut.error` 直接可见）；
- 走仓储的条件更新，多副本下只有一个能改到，不会误杀别人的活 run。
"""

from __future__ import annotations

import asyncio
import logging

from ..core.logging import log_event
from ..storage.base import AgentRepository

janitor_log = logging.getLogger("agent.janitor")

STALE_RUN_ERROR = "运行超过 {minutes} 分钟没有收尾（进程可能被强杀），已由巡检标记为已取消"


def stale_run_error(timeout_s: float) -> str:
    minutes = max(1, round(timeout_s / 60))
    return STALE_RUN_ERROR.format(minutes=minutes)


async def sweep_once(repo: AgentRepository, *, timeout_s: float) -> list[str]:
    """扫一轮，返回被收敛的 run id（空列表 = 没有脏数据）。"""
    return await repo.sweep_stale_runs(timeout_s, error=stale_run_error(timeout_s))


async def janitor_loop(repo: AgentRepository, *, timeout_s: float, interval_s: float) -> None:
    """按间隔巡检；单轮失败只记日志，不让循环死掉。"""
    while True:
        try:
            closed = await sweep_once(repo, timeout_s=timeout_s)
            if closed:
                log_event(
                    janitor_log,
                    logging.WARNING,
                    "stale runs reaped",
                    count=len(closed),
                    sample=closed[:5],
                    timeout_s=timeout_s,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # 巡检不能因为一次数据库抖动就退出
            log_event(
                janitor_log,
                logging.ERROR,
                "run sweep failed",
                error=f"{type(exc).__name__}: {exc}",
            )
        await asyncio.sleep(interval_s)
