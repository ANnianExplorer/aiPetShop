"""HTTP 层的数据形状：请求体严格校验（extra=forbid），响应与 domain 解耦。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000, description="用户本轮输入")
    session_id: str | None = Field(default=None, max_length=32, description="会话ID；为空则新建")
    pet_id: str | None = Field(default=None, max_length=32, description="本轮聚焦的宠物ID")
    channel: Literal["app", "web", "internal"] = "app"
    client_message_id: str | None = Field(
        default=None,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]{1,64}$",
        description="客户端生成的幂等键；重试同一条消息时带上它，服务端不会重复执行",
    )


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    run_id: str | None = None
    citations: list[dict[str, str]] = Field(default_factory=list)
    create_time: str | None = None


class MessagesOut(BaseModel):
    session_id: str
    messages: list[MessageOut]


class SessionItemOut(BaseModel):
    """App 侧看到的会话摘要：不含 user_id（本来就是自己的）。"""

    id: str
    pet_id: str | None = None
    channel: str
    title: str
    message_count: int
    create_time: str | None = None


class SessionListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SessionItemOut]

class HealthOut(BaseModel):
    status: str
    repo: str
    model: str | None
    model_configured: bool
    model_source: str = "none"
    tools: list[str]
    graph_ready: bool
    auth_mode: str


class ModelConfigIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=32)
    base_url: str = Field(min_length=1, max_length=255)
    model: str = Field(min_length=1, max_length=128)
    api_key: str = Field(default="", max_length=512, repr=False)
    enabled: bool = True

    @field_validator("base_url")
    @classmethod
    def _check_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("base_url 必须以 http:// 或 https:// 开头")
        return normalized


class ModelConfigOut(BaseModel):
    provider: str
    base_url: str
    model: str
    enabled: bool
    source: str
    has_api_key: bool
    api_key_masked: str
    updated_by: str | None = None
    update_time: str | None = None
    fallback: str
    runtime_model: str | None = None
    runtime_source: str
    error: str | None = None


class ModelConfigTestOut(BaseModel):
    ok: bool
    latency_ms: int
    model: str
    provider: str


class UsageOut(BaseModel):
    days: int
    runs: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    avg_latency_ms: int


class MemoryFactOut(BaseModel):
    id: str
    key: str
    label: str
    value: str
    confidence: float
    update_time: str | None = None


class MemoryOut(BaseModel):
    pet_id: str | None
    facts: list[MemoryFactOut]


class MemoryExportOut(BaseModel):
    """用户数据导出：版本号是为了将来字段变更时，导入方能识别格式。"""

    version: int = 1
    exported_at: str
    pet_id: str | None = None
    facts: list[MemoryFactOut]


class ProfileOut(BaseModel):
    """画像快照：`data` 内部结构由 `build_profile` 决定，对外按 JSON 原样透出。"""

    id: str
    user_id: str | None = None
    pet_id: str | None = None
    version: int
    fact_count: int
    confidence: float
    create_time: str | None = None
    # 事实比这份画像新时为 True：前端据此提示「有更新，建议重算」
    stale: bool = False
    data: dict[str, Any]


class ProfileListOut(BaseModel):
    total: int
    items: list[ProfileOut]


class GraphNodeOut(BaseModel):
    id: str
    kind: str  # pet / fact / event
    label: str
    detail: str | None = None


class GraphEdgeOut(BaseModel):
    source: str
    target: str
    kind: str  # remembered / happened
    label: str | None = None


class AdminGraphOut(BaseModel):
    """管理端知识图谱：以「宠物」为中心，连记忆事实与最近对话事件。

    只画 Agent 自己库里的数据（memory_fact / agent_run），不反查业务库——
    业务真源在 Java，跨服务拼图容易把权限边界拼漏。
    """

    user_id: str
    pet_id: str | None = None
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


class ErrorOut(BaseModel):
    code: str
    message: str
    retryable: bool = False
    detail: dict[str, Any] | None = None


# ---------------------------------------------------------------- 管理端（只读）


class AdminSessionItem(BaseModel):
    id: str
    user_id: str
    pet_id: str | None = None
    channel: str
    title: str
    message_count: int
    create_time: str | None = None


class AdminSessionList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminSessionItem]


class AdminStepOut(BaseModel):
    seq: int
    kind: str
    name: str
    status: str
    latency_ms: int
    error: str | None = None


class AdminRunOut(BaseModel):
    id: str
    route: str
    intent: str
    status: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    error: str | None = None
    steps: list[AdminStepOut]


class AdminSessionDetail(BaseModel):
    session: AdminSessionItem
    messages: list[MessageOut]
    runs: list[AdminRunOut]


class AdminDayUsage(BaseModel):
    day: str
    runs: int
    tokens: int


class AdminUsageOut(BaseModel):
    days: int
    runs: int
    users: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    avg_latency_ms: int
    by_day: list[AdminDayUsage]


class AdminTaskTopicOut(BaseModel):
    """一个 topic 的现场：还没消费的、卡在死信里的。"""

    topic: str
    depth: int
    dead_letters: int


class AdminTasksOut(BaseModel):
    """`TASK_BACKEND=off` 时 `enabled=false`，两个计数恒为 0——不是故障，是没启用。"""

    enabled: bool
    backend: str
    processed: int
    failed: int
    topics: list[AdminTaskTopicOut]


class ReplayDeadLetterRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=64)
    limit: int = Field(default=10, ge=1, le=100)


class ReplayDeadLetterOut(BaseModel):
    topic: str
    replayed: int


# ---------------------------------------------------------------- 文档问答（RAG）


class DocumentOut(BaseModel):
    id: str
    name: str
    mime: str
    size_bytes: int
    pet_id: str | None = None
    status: int
    status_label: str
    error: str | None = None
    chunk_count: int
    create_time: str | None = None


class DocumentListOut(BaseModel):
    total: int
    items: list[DocumentOut]


class CapabilityGroup(BaseModel):
    supported: bool
    suffixes: list[str] = Field(default_factory=list)
    reason: str | None = None


class CapabilitiesOut(BaseModel):
    text: CapabilityGroup
    pdf: CapabilityGroup
    image: CapabilityGroup
    video: CapabilityGroup
    embedder: dict[str, Any]
    max_bytes: int
