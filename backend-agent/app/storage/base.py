"""存储契约：会话 / 消息 / 运行 / 步骤。

四个不变量（memory 与 mysql 两套实现都必须满足，测试用同一套断言跑）：
1. 会话有主：`session_id` 存在但属于别的用户 → 抛 `Forbidden`，绝不"顺手新建"；
2. 消息顺序：`history()` 必须按时间正序返回，且只含 user/assistant；
3. 步骤序号：同一 run 内 `seq` 从 1 连续递增，跨 run 不串；
4. 运行终态：`finish_run` 之后 status 只能是 succeeded/failed/cancelled，不允许再改。
"""

from __future__ import annotations

from typing import Any, Protocol

from ..domain.models import (
    MemoryFact,
    Message,
    Run,
    RunDetail,
    RunStatus,
    Session,
    SessionSummary,
    Step,
    Usage,
    UsageOverview,
    UsageSummary,
)
from ..rag.models import Chunk, Document, DocumentStatus


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

    async def find_run_by_idempotency(self, user_id: str, idempotency_key: str) -> Run | None:
        """按幂等键查已有运行；查不到返回 None。

        按**用户**而不是会话去重：首次请求可能失败在「会话还没建出来」之前，
        客户端此时拿不到 session_id，重试只能重发同一条消息；
        若按会话去重，重试会新建会话再执行一遍，幂等就失效了。

        唯一键 `(user_id, idempotency_key)` 在库层兜底：并发重复提交时，
        `start_run` 会撞唯一键并回查已有 run，保证「一条消息最多一次执行」。
        """
        ...

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
        *,
        event_id: str | None = None,
    ) -> None: ...

    async def history(self, session_id: str, limit: int) -> list[dict[str, Any]]: ...

    async def list_messages(self, session_id: str, limit: int = 50) -> list[Message]: ...

    async def ping(self) -> None:
        """就绪探针：连接可用则正常返回，否则抛异常（/readyz 据此判定 503）。"""
        ...

    # ---- 长期记忆 ----
    async def get_memory_fact(
        self, user_id: str, pet_id: str | None, key: str
    ) -> MemoryFact | None: ...

    async def upsert_memory_fact(self, fact: MemoryFact) -> MemoryFact: ...

    async def list_memory_facts(
        self, user_id: str, pet_id: str | None, limit: int = 10
    ) -> list[MemoryFact]: ...

    async def delete_memory_fact(self, user_id: str, pet_id: str | None, key: str) -> bool:
        """删除一条事实，返回是否真的删到了（False → 接口层 404）。

        物理删除：这是用户行使删除权，不是管理端审计场景；
        `pet_id=None` 与 `pet_id=0` 视为同一槽位（与 `uk_user_pet_key` 一致）。
        """
        ...

    # ---- 用量 ----
    async def usage_summary(self, user_id: str, since: str | None = None) -> UsageSummary: ...

    # ---- 管理端只读（调用方必须先校验 admin 角色，仓储层不做权限判断） ----
    async def list_sessions(
        self,
        *,
        page: int,
        page_size: int,
        user_id: str | None = None,
        query: str | None = None,
    ) -> tuple[int, list[SessionSummary]]:
        """分页列出会话：返回 (总数, 当前页)。排序固定为最近活跃在前。"""
        ...

    async def get_session_any(self, session_id: str) -> Session | None:
        """无条件按 id 取会话（管理员视角）；普通用户路径不要用这个。"""
        ...

    async def list_runs(self, session_id: str) -> list[RunDetail]:
        """某会话的全部运行轨迹（含 steps），按时间正序。"""
        ...

    async def usage_overview(self, since: str | None = None) -> UsageOverview:
        """全局用量：总量 + 按天趋势，只统计 succeeded 的 run。"""
        ...

    # ---- 文档问答（RAG）----
    # 契约：所有读写都带 user_id；`get_document` / `delete_document` 传别人 id 返回 None，
    # 不抛异常（接口层统一 404，避免泄露"存在但不属于你"）。
    async def create_document(self, document: Document) -> Document:
        """落一条文档记录；同一用户同 sha 已存在时返回既有记录（去重）。"""
        ...

    async def get_document(self, user_id: str, document_id: str) -> Document | None: ...

    async def get_document_by_sha(self, user_id: str, sha256: str) -> Document | None: ...

    async def list_documents(
        self, user_id: str, *, pet_id: str | None = None, limit: int = 50
    ) -> list[Document]: ...

    async def update_document(
        self,
        document_id: str,
        *,
        status: DocumentStatus | None = None,
        error: str | None = None,
        chunk_count: int | None = None,
    ) -> Document:
        """只改状态机字段；文档不存在抛 NotFound（由上层兜）。"""
        ...

    async def delete_document(self, user_id: str, document_id: str) -> bool:
        """软删文档 + 硬删其切片，返回是否删到。"""
        ...

    async def add_chunks(self, chunks: list[Chunk]) -> None: ...

    async def list_chunks(
        self, user_id: str, *, pet_id: str | None = None, limit: int = 2000
    ) -> list[Chunk]:
        """检索用：只返回该用户的块，按创建时间倒序截断。"""
        ...

    async def aclose(self) -> None: ...
