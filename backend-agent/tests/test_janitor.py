"""僵尸 run 收敛：进程被强杀后，`agent_run` 不能永远停在 `running`。

判据用「开始时间」，所以测试里把 `created` 往前拨——这比 `sleep` 真实等待便宜得多，
也不会让 CI 变慢。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import pytest
from conftest import make_http, make_settings

from app.api.app import create_app
from app.domain.models import Intent, Route, Run, RunStatus, Usage
from app.runtime.janitor import STALE_RUN_ERROR, janitor_loop, stale_run_error, sweep_once
from app.storage.memory import InMemoryRepository

_TIME_FMT = "%Y-%m-%d %H:%M:%S.%f"


async def _seed_run(repo: InMemoryRepository, *, age_s: float = 0.0) -> tuple[str, str]:
    """建一个 running 的 run；`age_s > 0` 时把创建时间往前拨。返回 (session_id, run_id)。"""
    session = await repo.get_or_create_session(None, "1001", None, "app", "巡检会话")
    run = await repo.start_run(
        Run(
            id="",
            session_id=session.id,
            user_message_id="",
            route=Route.L1,
            intent=Intent.CHAT,
            model="scripted",
            user_id="1001",
        )
    )
    if age_s > 0:
        repo._runs[run.id]["created"] = (datetime.now() - timedelta(seconds=age_s)).strftime(
            _TIME_FMT
        )
    return session.id, run.id


async def test_sweep_marks_stale_run_cancelled() -> None:
    repo = InMemoryRepository()
    sid, run_id = await _seed_run(repo, age_s=3600)

    closed = await sweep_once(repo, timeout_s=900)

    assert closed == [run_id]
    stored = await repo.get_run(run_id)
    assert stored is not None and stored.status is RunStatus.CANCELLED
    detail = (await repo.list_runs(sid))[0]
    # 管理端 `AdminRunOut.error` 直接取这个字段，原因必须是人能看懂的一句话
    assert detail.error == stale_run_error(900)
    assert "15 分钟" in detail.error
    assert STALE_RUN_ERROR.format(minutes=15) == detail.error
    assert detail.latency_ms >= 3600 * 1000


async def test_sweep_skips_fresh_and_finished_runs() -> None:
    repo = InMemoryRepository()
    _sid, fresh_id = await _seed_run(repo, age_s=0)
    _, old_id = await _seed_run(repo, age_s=3600)
    # 老 run 先正常收尾：巡检不该把已经结束的再改一遍
    await repo.finish_run(old_id, RunStatus.SUCCEEDED, Usage(), latency_ms=10)

    closed = await sweep_once(repo, timeout_s=900)

    assert closed == []
    fresh = await repo.get_run(fresh_id)
    assert fresh is not None and fresh.status is RunStatus.RUNNING
    finished = await repo.get_run(old_id)
    assert finished is not None and finished.status is RunStatus.SUCCEEDED


async def test_sweep_is_idempotent() -> None:
    repo = InMemoryRepository()
    _, run_id = await _seed_run(repo, age_s=3600)

    assert await sweep_once(repo, timeout_s=900) == [run_id]
    # 第二遍必须空手而归：多副本/多轮巡检不能重复处理同一行
    assert await sweep_once(repo, timeout_s=900) == []


async def test_janitor_loop_reaps_then_keeps_running() -> None:
    repo = InMemoryRepository()
    _, run_id = await _seed_run(repo, age_s=3600)
    task = asyncio.create_task(janitor_loop(repo, timeout_s=900, interval_s=0.05))
    try:
        for _ in range(100):
            stored = await repo.get_run(run_id)
            if stored is not None and stored.status is RunStatus.CANCELLED:
                break
            await asyncio.sleep(0.01)
        stored = await repo.get_run(run_id)
        assert stored is not None and stored.status is RunStatus.CANCELLED
        assert not task.done(), "巡检循环扫完一轮就退出，等于没有巡检"
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_lifespan_reaps_on_startup() -> None:
    """进程重启的第一件事就是收尸：旧进程留下的僵尸 run 必须在上线前收敛。"""
    settings = make_settings()
    repo = InMemoryRepository()
    sid, run_id = await _seed_run(repo, age_s=3600)

    app = create_app(settings, repo=repo, http_client=make_http())
    async with app.router.lifespan_context(app):  # type: ignore[attr-defined]
        stored = await repo.get_run(run_id)
        assert stored is not None and stored.status is RunStatus.CANCELLED

    detail = (await repo.list_runs(sid))[0]
    assert detail.error and "巡检" in detail.error


def test_stale_timeout_must_exceed_run_deadline(settings: Any) -> None:
    """配置层面的护栏：阈值小于运行超时，会把还在正常跑的 run 误判成僵尸。"""
    assert settings.stale_run_timeout_s > settings.run_deadline_s
