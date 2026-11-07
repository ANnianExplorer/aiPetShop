"""文档服务：接收 → 落盘 → 解析 → 切分 → 嵌入 → 可检索。

三条不变量：
1. 同一用户同一内容只解析一次（`uk_user_sha` + 这里先查再建）；
2. 解析失败/不支持都要落 `status` 与可读原因，绝不静默；
3. 检索永远带 `user_id` 过滤，`pet_id` 只是进一步收窄。
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from pathlib import Path

from ..core.ids import IdGenerator
from ..core.logging import log_event
from .chunker import chunk_text
from .embedder import Embedder, cosine
from .media import FfmpegMedia, detect_media
from .models import Chunk, ChunkHit, Document, DocumentStatus
from .ocr import OcrEngine, UnsupportedMedia, detect_ocr
from .parsers import parse_document

rag_log = logging.getLogger("agent.rag")

MAX_BYTES = 20 * 1024 * 1024
MAX_CHUNKS = 400
MIN_SCORE = 0.05


class DocumentService:
    def __init__(
        self,
        repository,
        embedder: Embedder,
        *,
        storage_dir: Path | str = "data/docs",
        ocr: OcrEngine | None = None,
        media: FfmpegMedia | None = None,
        ids: IdGenerator | None = None,
        max_bytes: int = MAX_BYTES,
        min_score: float = MIN_SCORE,
    ) -> None:
        self._repo = repository
        self._embedder = embedder
        self._dir = Path(storage_dir)
        self._ocr = ocr or detect_ocr()
        self._media = media or detect_media()
        self._ids = ids or IdGenerator(node_id=7)
        self._max_bytes = max_bytes
        self._min_score = min_score

    # ---- 能力矩阵：前端据此决定"能不能传图片/视频" ----
    def capabilities(self) -> dict[str, object]:
        return {
            "text": {"supported": True, "suffixes": ["txt", "md", "csv", "json", "log", "yaml"]},
            "pdf": {"supported": True, "suffixes": ["pdf"]},
            "image": {
                "supported": self._ocr.available,
                "suffixes": ["png", "jpg", "jpeg", "webp", "bmp"],
                "reason": None if self._ocr.available else "服务器未安装 OCR（tesseract）",
            },
            "video": {
                "supported": self._media.available and self._ocr.available,
                "suffixes": ["mp4", "mov", "avi", "mkv", "webm"],
                "reason": None
                if self._media.available and self._ocr.available
                else "服务器未安装 ffmpeg/OCR",
            },
            "embedder": {"backend": self._embedder.name, "dim": self._embedder.dim},
            "max_bytes": self._max_bytes,
        }

    def storage_path(self, user_id: str, sha256: str) -> Path:
        return self._dir / user_id / f"{sha256}.bin"

    async def ingest(
        self,
        *,
        user_id: str,
        name: str,
        mime: str,
        data: bytes,
        pet_id: str | None = None,
    ) -> Document:
        if not data:
            raise ValueError("文件为空")
        if len(data) > self._max_bytes:
            raise ValueError(f"文件超过 {self._max_bytes // (1024 * 1024)}MB 上限")

        sha = hashlib.sha256(data).hexdigest()
        existing = await self._repo.get_document_by_sha(user_id, sha)
        if existing is not None:
            log_event(rag_log, logging.INFO, "document reused", document=existing.id, sha=sha[:12])
            return existing

        path = self.storage_path(user_id, sha)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

        document = Document(
            id=self._ids.next(),
            user_id=user_id,
            pet_id=pet_id,
            name=name[:255],
            mime=mime[:128],
            size_bytes=len(data),
            sha256=sha,
            storage_key=str(path.relative_to(self._dir)).replace("\\", "/"),
            status=DocumentStatus.QUEUED,
        )
        created = await self._repo.create_document(document)
        log_event(
            rag_log,
            logging.INFO,
            "document queued",
            document=created.id,
            doc_name=created.name,
            size=created.size_bytes,
        )
        return created

    async def process(self, document: Document) -> Document:
        """解析一篇文档；异常分两类落状态：不支持 vs 真失败。"""
        await self._repo.update_document(document.id, status=DocumentStatus.PARSING)
        path = self._dir / document.storage_key
        try:
            if not path.exists():
                raise FileNotFoundError(f"文件已丢失：{document.storage_key}")
            segments = await parse_document(
                name=document.name,
                mime=document.mime,
                data=path.read_bytes(),
                ocr=self._ocr,
                media=self._media,
            )
            chunks = self._chunk_segments(document, segments)
            if not chunks:
                raise UnsupportedMedia("没有切出可检索的内容")
            vectors = await self._embedder.embed([c.content for c in chunks])
            for chunk, vector in zip(chunks, vectors, strict=True):
                chunk.embedding = vector
            await self._repo.add_chunks(chunks)
            ready = await self._repo.update_document(
                document.id,
                status=DocumentStatus.READY,
                error=None,
                chunk_count=len(chunks),
            )
            log_event(
                rag_log,
                logging.INFO,
                "document ready",
                document=document.id,
                chunks=len(chunks),
                embedder=self._embedder.name,
            )
            return ready
        except UnsupportedMedia as exc:
            failed = await self._repo.update_document(
                document.id, status=DocumentStatus.UNSUPPORTED, error=str(exc)[:500]
            )
            log_event(rag_log, logging.WARNING, "document unsupported",
                      document=document.id, reason=str(exc))
            return failed
        except Exception as exc:  # 解析异常不能把 worker 打崩
            failed = await self._repo.update_document(
                document.id,
                status=DocumentStatus.FAILED,
                error=f"{exc.__class__.__name__}: {str(exc)[:400]}",
            )
            log_event(rag_log, logging.ERROR, "document failed",
                      document=document.id, error=exc.__class__.__name__)
            return failed

    def _chunk_segments(self, document: Document, segments: Sequence) -> list[Chunk]:
        chunks: list[Chunk] = []
        for segment in segments:
            for piece in chunk_text(segment.text):
                if len(chunks) >= MAX_CHUNKS:
                    return chunks
                chunks.append(
                    Chunk(
                        id=self._ids.next(),
                        file_id=document.id,
                        user_id=document.user_id,
                        pet_id=document.pet_id,
                        chunk_index=len(chunks),
                        locator=segment.locator,
                        content=piece,
                        token_hint=len(piece),
                    )
                )
        return chunks

    async def search(
        self,
        *,
        user_id: str,
        query: str,
        pet_id: str | None = None,
        top_k: int = 5,
    ) -> list[ChunkHit]:
        query = (query or "").strip()
        if not query:
            return []
        query_vec = (await self._embedder.embed([query]))[0]
        rows = await self._repo.list_chunks(user_id, pet_id=pet_id, limit=2000)
        names: dict[str, str] = {}
        hits: list[ChunkHit] = []
        for chunk in rows:
            if not chunk.embedding or len(chunk.embedding) != len(query_vec):
                continue
            score = cosine(query_vec, chunk.embedding)
            if score < self._min_score:
                continue
            if chunk.file_id not in names:
                doc = await self._repo.get_document(user_id, chunk.file_id)
                names[chunk.file_id] = doc.name if doc else ""
            hits.append(ChunkHit(chunk=chunk, score=round(score, 4), document_name=names[chunk.file_id]))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: max(1, min(top_k, 20))]

    async def get(self, user_id: str, document_id: str) -> Document | None:
        return await self._repo.get_document(user_id, document_id)

    async def list(self, user_id: str, *, pet_id: str | None = None, limit: int = 50) -> list[Document]:
        return await self._repo.list_documents(user_id, pet_id=pet_id, limit=limit)

    async def delete(self, user_id: str, document_id: str) -> bool:
        removed = await self._repo.delete_document(user_id, document_id)
        if removed:
            log_event(rag_log, logging.INFO, "document deleted", document=document_id)
        return removed
