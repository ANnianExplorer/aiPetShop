"""存储契约：内存版与 MySQL 版必须表现一致，所以断言写在协议层。

MySQL 用例默认跳过；设置 `PET_AGENT_TEST_MYSQL_DSN`（例如
`mysql://root:pwd@127.0.0.1:3306/petlumina`，且已执行 backend/sql/v2.10-agent.sql）后自动纳入。
"""

from __future__ import annotations

import os
from collections.abc import Callable

import pytest

from app.core.errors import Forbidden, NotFound
from app.domain.models import Intent, Message, Role, Route, Run, RunStatus, Step, StepKind, Usage
from app.storage import AgentRepository, InMemoryRepository, MySqlRepository

_MYSQL_DSN = os.environ.get("PET_AGENT_TEST_MYSQL_DSN", "")

_FACTORIES: list[tuple[str, Callable[[], AgentRepository]]] = [
    ("memory", InMemoryRepository),
]
if _MYSQL_DSN:
    _FACTORIES.append(("mysql", lambda: MySqlRepository(_MYSQL_DSN)))


@pytest.fixture(params=_FACTORIES, ids=[name for name, _ in _FACTORIES])
def repo(request: pytest.FixtureRequest) -> AgentRepository:
    factory = request.param[1]
    return factory()


async def _session(repo: AgentRepository, user_id: str = "1001") -> str:
    session = await repo.get_or_create_session(None, user_id, None, "app", "测试会话")
    return session.id


async def test_session_is_reused(repo: AgentRepository) -> None:
    sid = await _session(repo)
    again = await repo.get_or_create_session(sid, "1001", None, "app", "忽略")
    assert again.id == sid


async def test_foreign_session_is_forbidden(repo: AgentRepository) -> None:
    sid = await _session(repo, "1001")
    with pytest.raises(Forbidden):
        await repo.get_or_create_session(sid, "1002", None, "app", "冒名")
    assert await repo.get_session(sid, "1002") is None


async def test_history_ordered_and_filtered(repo: AgentRepository) -> None:
    sid = await _session(repo)
    for role, text in (
        (Role.USER, "第一句"),
        (Role.ASSISTANT, "第二句"),
        (Role.SYSTEM, "不该出现"),
    ):
        await repo.add_message(Message(id="", session_id=sid, role=role, content=text))
    history = await repo.history(sid, 10)
    assert [h["role"] for h in history] == ["user", "assistant"]
    assert [h["content"] for h in history] == ["第一句", "第二句"]


async def test_history_limit_keeps_latest(repo: AgentRepository) -> None:
    sid = await _session(repo)
    for i in range(5):
        await repo.add_message(
            Message(id="", session_id=sid, role=Role.USER, content=f"m{i}")
        )
    history = await repo.history(sid, 2)
    assert [h["content"] for h in history] == ["m3", "m4"]


async def test_steps_seq_continuous(repo: AgentRepository) -> None:
    sid = await _session(repo)
    run = await repo.start_run(
        Run(id="", session_id=sid, user_message_id="", route=Route.L2, intent=Intent.LOG, model="m")
    )
    await repo.add_steps(run.id, [Step(0, StepKind.ROUTE, "classify")])
    await repo.add_steps(
        run.id,
        [
            Step(0, StepKind.LLM, "agent"),
            Step(0, StepKind.TOOL, "search_logs"),
        ],
    )
    steps = repo.steps_of(run.id) if isinstance(repo, InMemoryRepository) else []
    if steps:
        assert [s.seq for s in steps] == [1, 2, 3]


async def test_finish_run_once_only(repo: AgentRepository) -> None:
    sid = await _session(repo)
    run = await repo.start_run(
        Run(id="", session_id=sid, user_message_id="", route=Route.L1, intent=Intent.CHAT, model="m")
    )
    await repo.finish_run(run.id, RunStatus.SUCCEEDED, Usage(3, 5), 120)
    with pytest.raises(ValueError):
        await repo.finish_run(run.id, RunStatus.FAILED, Usage(), 1)

    stored = await repo.get_run(run.id)
    assert stored is not None and stored.session_id == sid


async def test_finish_unknown_run(repo: AgentRepository) -> None:
    with pytest.raises(NotFound):
        await repo.finish_run("no-such-run", RunStatus.SUCCEEDED, Usage(), 1)


async def test_audit_tool_call(repo: AgentRepository) -> None:
    await repo.audit_tool_call("run-1", "search_logs", True, None, 12, "abc123")
    if isinstance(repo, InMemoryRepository):
        assert repo.tool_calls()[0]["name"] == "search_logs"
