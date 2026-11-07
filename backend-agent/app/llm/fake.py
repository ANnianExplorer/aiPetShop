"""脚本化模型：测试与评测专用。按预设脚本出牌，并记录每次收到的上下文。"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from ..domain.models import Usage
from .base import ChatModel, LLMReply, StreamChunk


class ScriptedModel(ChatModel):
    def __init__(
        self,
        replies: Sequence[LLMReply] | None = None,
        *,
        chunks: Sequence[str] = ("我在", "呢。"),
        usage: Usage | None = None,
        fallback_text: str = "我在呢。",
        fail_complete: Exception | None = None,
        fail_stream: Exception | None = None,
    ) -> None:
        self._replies = list(replies or [])
        self._chunks = list(chunks)
        self._usage = usage or Usage(10, 4)
        self._fallback_text = fallback_text
        self._fail_complete = fail_complete
        self._fail_stream = fail_stream
        self.calls: list[list[dict[str, Any]]] = []
        self.tool_names: list[str] = []

    @property
    def name(self) -> str:
        return "scripted"

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> LLMReply:
        self.calls.append([dict(m) for m in messages])
        self.tool_names = [t["function"]["name"] for t in (tools or [])]
        if self._fail_complete is not None:
            raise self._fail_complete
        if not self._replies:
            return LLMReply(text=self._fallback_text, usage=self._usage)
        return self._replies.pop(0)

    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[StreamChunk]:
        if self._fail_stream is not None:
            raise self._fail_stream
        for chunk in self._chunks:
            yield StreamChunk(text=chunk)
        yield StreamChunk(usage=self._usage)

    async def aclose(self) -> None:
        return None
