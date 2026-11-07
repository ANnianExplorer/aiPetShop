"""HTTP 层的数据形状：请求体严格校验（extra=forbid），响应与 domain 解耦。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class HealthOut(BaseModel):
    status: str
    repo: str
    model: str | None
    model_configured: bool
    tools: list[str]
    graph_ready: bool
    auth_mode: str


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
