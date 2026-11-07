"""内存实现：零依赖，单测与本地开发用；语义必须与 MySQL 版一致。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..core.errors import Forbidden, NotFound
from ..core.ids import new_id
from ..domain.models import Message, Role, Run, RunStatus, Session, Step, Usage


class InMemoryRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._messages: dict[str, list[Message]] = {}
        self._runs: dict[str, dict[str, Any]] = {}
        self._steps: dict[str, list[Step]] = {}
        self._tool_calls: list[dict[str, Any]] = []

    # ------------------------------------------------------------ 会话
    async def get_or_create_session(
        self,
        session_id: str | None,
        user_id: str,
        pet_id: str | None,
        channel: str,
        title: str,
    ) -> Session:
        if session_id:
            existing = self._sessions.get(session_id)
            if existing is not None:
                if existing.user_id != user_id:
                    # 不暴露"该会话存在"这一事实，统一按无权限处理
                    raise Forbidden("会话不属于当前用户")
                return existing
        sid = session_id or new_id()
        session = Session(
            id=sid,
            user_id=user_id,
            channel=channel,
            pet_id=pet_id,
            title=title[:64],
            create_time=_now(),
        )
        self._sessions[sid] = session
        self._messages.setdefault(sid, [])
        return session

    async def get_session(self, session_id: str, user_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None or session.user_id != user_id:
            return None
        return session

    # ------------------------------------------------------------ 消息
    async def add_message(self, msg: Message) -> Message:
        if not msg.id:
            msg.id = new_id()
        msg.create_time = msg.create_time or _now()
        self._messages.setdefault(msg.session_id, []).append(msg)
        return msg

    async def history(self, session_id: str, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        msgs = [
            m
            for m in self._messages.get(session_id, [])
            if m.role in (Role.USER, Role.ASSISTANT)
        ][-limit:]
        return [{"role": m.role.value, "content": m.content} for m in msgs]

    async def list_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        return list(self._messages.get(session_id, [])[-limit:])

    # ------------------------------------------------------------ 运行
    async def start_run(self, run: Run) -> Run:
        if not run.id:
            run.id = new_id()
        self._runs[run.id] = {
            "run": run,
            "status": RunStatus.RUNNING,
            "error": None,
            "usage": Usage(),
            "latency_ms": 0,
        }
        self._steps.setdefault(run.id, [])
        return run

    async def get_run(self, run_id: str) -> Run | None:
        record = self._runs.get(run_id)
        return record["run"] if record else None

    async def add_steps(self, run_id: str, steps: list[Step], start_seq: int = 1) -> None:
        bucket = self._steps.setdefault(run_id, [])
        if bucket:
            start_seq = max(start_seq, bucket[-1].seq + 1)
        for offset, step in enumerate(steps):
            step.seq = start_seq + offset
            bucket.append(step)

    async def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        usage: Usage,
        latency_ms: int,
        error: str | None = None,
    ) -> None:
        record = self._runs.get(run_id)
        if record is None:
            raise NotFound(f"运行不存在：{run_id}")
        current: RunStatus = record["status"]
        if current is not RunStatus.RUNNING:
            raise ValueError(f"运行已处于终态 {current.value}，不能再次结束")
        record.update({"status": status, "usage": usage, "latency_ms": latency_ms, "error": error})

    async def audit_tool_call(
        self,
        run_id: str,
        name: str,
        ok: bool,
        code: str | None,
        latency_ms: int,
        args_digest: str,
    ) -> None:
        self._tool_calls.append(
            {
                "id": new_id(),
                "run_id": run_id,
                "name": name,
                "ok": ok,
                "code": code,
                "latency_ms": latency_ms,
                "args_digest": args_digest,
            }
        )

    # ------------------------------------------------------------ 测试辅助
    def steps_of(self, run_id: str) -> list[Step]:
        return list(self._steps.get(run_id, []))

    def run_record(self, run_id: str) -> dict[str, Any]:
        return dict(self._runs.get(run_id, {}))

    def tool_calls(self) -> list[dict[str, Any]]:
        return list(self._tool_calls)

    async def ping(self) -> None:
        # 内存实现永远可用；保留此方法是为了让 /readyz 不必区分实现
        return None

    async def aclose(self) -> None:
        return None


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
