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
class Session:
    id: str
    user_id: str
    channel: str
    pet_id: str | None = None
    title: str = ""
    create_time: str | None = None


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
