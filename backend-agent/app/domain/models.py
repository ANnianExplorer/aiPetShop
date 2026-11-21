"""领域模型：不依赖 IO、不依赖框架，图/存储/接口三处共用同一套类型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Intent(str, Enum):
    CHAT = "chat"
    HEALTH = "health"
    LOG = "log"
    PROFILE = "profile"


class Route(str, Enum):
    """L1 直答 / L2 ReAct 工具循环 / L3 Plan-Execute（S4 才开）。"""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class StepKind(str, Enum):
    ROUTE = "route"
    LLM = "llm"
    TOOL = "tool"
    REFLECT = "reflect"


class StepStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    DENIED = "denied"
    PROPOSED = "proposed"


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_CONFIRMATION = "awaiting_confirmation"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


@dataclass(frozen=True)
class Citation:
    """回答里可点回的来源。locator 是给人用的定位串（日期 / 页码 / 时间戳）。"""

    kind: str
    id: str
    label: str = ""
    locator: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "id": self.id, "label": self.label, "locator": self.locator}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Citation:
        return cls(
            kind=str(raw.get("kind") or "record"),
            id=str(raw.get("id") or ""),
            label=str(raw.get("label") or ""),
            locator=str(raw.get("locator") or ""),
        )


def dedupe_citations(items: list[Citation]) -> list[Citation]:
    """按 (kind, id) 去重且保持顺序；空 id 一律丢弃（脏数据不进展示）。"""
    seen: set[tuple[str, str]] = set()
    out: list[Citation] = []
    for item in items:
        if not item.id:
            continue
        key = (item.kind, item.id)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


@dataclass
class MemoryFact:
    """长期事实记忆：一条 `(user, pet, key) → value`。

    `confidence` 由抽取规则给出，`source` 记录来源（conversation / manual），
    后续做"记忆可信度衰减"和"用户可纠正"都依赖这两个字段。
    """

    id: str
    user_id: str
    key: str
    value: str
    pet_id: str | None = None
    confidence: float = 0.8
    source: str = "conversation"
    create_time: str | None = None
    update_time: str | None = None


@dataclass
class MemoryEpisode:
    """情景记忆：一条「发生过的事」，带发生日期与来源消息 id。

    `occurred_at` 是事件发生时间（不是入库时间），当前只精确到日；
    `source_message_id` 既用于追溯原话，也用于旁路任务重复消费时的幂等。
    """

    id: str
    user_id: str
    summary: str
    occurred_at: str
    pet_id: str | None = None
    session_id: str | None = None
    source_message_id: str | None = None
    kind: str = ""
    detail: dict[str, Any] = field(default_factory=dict)
    create_time: str | None = None


@dataclass(frozen=True)
class ProfileSnapshot:
    """画像快照：同一 `(user, pet)` 追加式版本，不覆盖历史。

    `data` 是结构化画像（basics/traits/preferences/riskFlags/careGaps/evidence），
    每条结论都能通过 `evidence[].factId` 回放到 `memory_fact`。
    """

    id: str
    user_id: str
    pet_id: str | None
    version: int
    data: dict[str, Any]
    fact_count: int = 0
    confidence: float = 0.0
    create_time: str | None = None


@dataclass(frozen=True)
class UsageSummary:
    """按用户聚合的用量：给「我这个月花了多少 token」这类问题提供数据。"""
    runs: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    avg_latency_ms: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class Session:
    id: str
    user_id: str
    channel: str
    pet_id: str | None = None
    title: str = ""
    create_time: str | None = None
    message_count: int = 0


@dataclass(frozen=True)
class SessionSummary:
    """管理端列表用的会话摘要：只带列表需要的字段，不把整条消息流拖出来。"""

    id: str
    user_id: str
    pet_id: str | None
    channel: str
    title: str
    message_count: int
    create_time: str | None

    @classmethod
    def of(cls, session: Session) -> SessionSummary:
        return cls(
            id=session.id,
            user_id=session.user_id,
            pet_id=session.pet_id,
            channel=session.channel,
            title=session.title,
            message_count=session.message_count,
            create_time=session.create_time,
        )


@dataclass(frozen=True)
class RunDetail:
    """一次运行的完整轨迹：管理端"它到底做了什么"就靠这个。"""

    id: str
    route: Route
    intent: Intent
    status: RunStatus
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    error: str | None = None
    steps: list[Step] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class DayUsage:
    day: str
    runs: int
    tokens: int


@dataclass(frozen=True)
class ModelUsage:
    """按模型拆分的用量：管理端回答"钱花在哪个模型上"。"""

    model: str
    runs: int
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class UsageOverview:
    """全局用量：管理端看"今天花了多少、谁在用"。"""

    runs: int = 0
    users: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    avg_latency_ms: int = 0
    by_day: list[DayUsage] = field(default_factory=list)
    by_model: list[ModelUsage] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class Message:
    id: str
    session_id: str
    role: Role
    content: str
    run_id: str | None = None
    citations: list[Citation] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    create_time: str | None = None


@dataclass
class Step:
    seq: int
    kind: StepKind
    name: str
    status: StepStatus = StepStatus.OK
    latency_ms: int = 0
    input: dict[str, Any] | None = None
    output_digest: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "kind": self.kind.value,
            "name": self.name,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


@dataclass
class Run:
    id: str
    session_id: str
    user_message_id: str
    route: Route
    intent: Intent
    model: str
    status: RunStatus = RunStatus.RUNNING
    # 用户维度：幂等键按 (user_id, idempotency_key) 去重，所以 run 必须自带 user_id。
    # 冗余一份是有意的——首次请求可能失败在"会话还没建出来"之前，此时只能靠用户定位重试。
    user_id: str = ""
    # 幂等键：客户端重试同一条消息时，用它找到已有 run 直接回放，不重复调用模型
    idempotency_key: str | None = None


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
        )


@dataclass
class ToolResult:
    """工具调用的统一返回：ok=False 也要带 code，模型才知道下一步该怎么改。"""

    ok: bool
    payload: dict[str, Any] = field(default_factory=dict)
    code: str | None = None
    error: str | None = None
    latency_ms: int = 0

    def to_model_content(self) -> str:
        if self.ok:
            return _dumps(self.payload)
        return _dumps({"ok": False, "code": self.code or "tool_failed", "error": self.error or ""})


def _dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False, default=str)
