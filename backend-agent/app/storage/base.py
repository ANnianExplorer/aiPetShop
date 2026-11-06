"""存储契约：会话 / 消息 / 运行 / 步骤。

四个不变量（memory 与 mysql 两套实现都必须满足，测试用同一套断言跑）：
1. 会话有主：`session_id` 存在但属于别的用户 → 抛 `Forbidden`，绝不"顺手新建"；
2. 消息顺序：`history()` 必须按时间正序返回，且只含 user/assistant；
3. 步骤序号：同一 run 内 `seq` 从 1 连续递增，跨 run 不串；
4. 运行终态：`finish_run` 之后 status 只能是 succeeded/failed/cancelled，不允许再改。
"""

from __future__ import annotations

from typing import Any, Protocol

from ..domain.models import Message, Run, RunStatus, Session, Step, Usage


class AgentRepository(Protocol):
    async def get_or_create_session(
        self,
        session_id: str | None,
        user_id: str,
        pet_id: str | None,
        channel: str,
        title: str,
    ) -> Session: ...

    async def get_session(self, session_id: str, user_id: str) -> Session | None: ...

    async def add_message(self, msg: Message) -> Message: ...

    async def start_run(self, run: Run) -> Run: ...

    async def get_run(self, run_id: str) -> Run | None: ...

    async def add_steps(self, run_id: str, steps: list[Step], start_seq: int = 1) -> None: ...

    async def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        usage: Usage,
        latency_ms: int,
        error: str | None = None,
    ) -> None: ...

    async def audit_tool_call(
        self,
        run_id: str,
        name: str,
        ok: bool,
        code: str | None,
        latency_ms: int,
        args_digest: str,
    ) -> None: ...

    async def history(self, session_id: str, limit: int) -> list[dict[str, Any]]: ...

    async def list_messages(self, session_id: str, limit: int = 50) -> list[Message]: ...

    async def aclose(self) -> None: ...
