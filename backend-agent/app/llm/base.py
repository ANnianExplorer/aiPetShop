"""模型层契约：图与运行时只认这个 Protocol，不认具体厂商。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ..domain.models import Usage


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    raw_arguments: str = ""
    parse_error: str | None = None


@dataclass(frozen=True)
class LLMReply:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


@dataclass(frozen=True)
class StreamChunk:
    """流式增量：要么是文本，要么是末段的用量统计（OpenAI 兼容实现只在最后给一次）。"""

    text: str | None = None
    usage: Usage | None = None


@runtime_checkable
class ChatModel(Protocol):
    name: str

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> LLMReply: ...

    def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[StreamChunk]: ...

    async def aclose(self) -> None: ...
