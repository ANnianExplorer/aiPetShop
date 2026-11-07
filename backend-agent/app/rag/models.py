"""RAG 域模型：文档、切片、检索命中。

约定：
- 对外 id 一律字符串（19 位雪花号超过 JS 安全整数）；
- `locator` 是引用回跳的唯一依据，格式固定为 `page=3` / `t=93s` / `offset=1200`；
- `status` 用状态机而不是布尔，解析失败要能带原因给用户看。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class DocumentStatus(IntEnum):
    QUEUED = 0
    PARSING = 1
    READY = 2
    FAILED = 3
    UNSUPPORTED = 4

    @property
    def label(self) -> str:
        return {
            DocumentStatus.QUEUED: "排队中",
            DocumentStatus.PARSING: "解析中",
            DocumentStatus.READY: "可检索",
            DocumentStatus.FAILED: "解析失败",
            DocumentStatus.UNSUPPORTED: "不支持",
        }[self]


@dataclass
class Document:
    id: str
    user_id: str
    name: str
    mime: str = ""
    size_bytes: int = 0
    sha256: str = ""
    storage_key: str = ""
    pet_id: str | None = None
    status: DocumentStatus = DocumentStatus.QUEUED
    error: str | None = None
    chunk_count: int = 0
    create_time: datetime | None = None


@dataclass
class Chunk:
    id: str
    file_id: str
    user_id: str
    chunk_index: int
    locator: str
    content: str
    embedding: list[float] = field(default_factory=list)
    pet_id: str | None = None
    token_hint: int = 0

    @property
    def dim(self) -> int:
        return len(self.embedding)


@dataclass
class ChunkHit:
    """一条检索命中：带着文档名与 locator，模型引用时能直接说清出处。"""

    chunk: Chunk
    score: float
    document_name: str

    def citation(self) -> dict[str, str]:
        return {
            "kind": "doc",
            "id": self.chunk.file_id,
            "label": self.document_name,
            "locator": self.chunk.locator,
        }
