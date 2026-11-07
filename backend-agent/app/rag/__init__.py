"""文档问答（RAG）子域。

对外只暴露三类东西：`DocumentService`（编排）、`build_embedder`（选后端）、
`ChunkHit`（检索结果，自带 citation）。
"""

from __future__ import annotations

from .embedder import Embedder, EmbedderError, HashEmbedder, OpenAICompatEmbedder, build_embedder, cosine
from .models import Chunk, ChunkHit, Document, DocumentStatus
from .ocr import NoopOcr, OcrEngine, TesseractOcr, UnsupportedMedia, detect_ocr
from .parsers import parse_document
from .service import DocumentService

__all__ = [
    "Chunk",
    "ChunkHit",
    "Document",
    "DocumentService",
    "DocumentStatus",
    "Embedder",
    "EmbedderError",
    "HashEmbedder",
    "NoopOcr",
    "OcrEngine",
    "OpenAICompatEmbedder",
    "TesseractOcr",
    "UnsupportedMedia",
    "build_embedder",
    "cosine",
    "detect_ocr",
    "parse_document",
]
