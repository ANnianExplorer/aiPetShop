"""流式事件协议。

四种事件就是 App 需要渲染的全部状态：路由 → 工具 → 文本增量 → 结束（或错误）。
编码只在一处：`encode_sse()`。断线续传靠 `id:`（事件序号）与 `GET /agent/runs/{id}/events`。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    ROUTE = "route"
    TOOL = "tool"
    DELTA = "delta"
    DONE = "done"
    ERROR = "error"


@dataclass(frozen=True)
class Event:
    type: EventType
    data: Mapping[str, Any] = field(default_factory=dict)
    seq: int = 0

    def with_seq(self, seq: int) -> Event:
        return Event(type=self.type, data=self.data, seq=seq)

    def to_sse(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False, default=str)
        return f"id: {self.seq}\nevent: {self.type.value}\ndata: {payload}\n\n"


def encode_sse(event: Event) -> str:
    return event.to_sse()
