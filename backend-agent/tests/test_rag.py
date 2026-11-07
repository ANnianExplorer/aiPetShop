"""文档问答（RAG）测试：切分、嵌入、解析分发、入库检索、租户隔离、HTTP 接口。

原则：不碰真 OCR/ffmpeg（本机也没装），用 NoopOcr 与假 media 走"不支持"分支；
PDF 分支用注入的假 pypdf 模块验证"按页取文本 + 空文本报扫描件"，不依赖真 PDF 文件。
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from conftest import AUTH_HEADERS

from app.rag.chunker import chunk_text
from app.rag.embedder import EmbedderError, HashEmbedder, cosine
from app.rag.models import DocumentStatus
from app.rag.ocr import NoopOcr, UnsupportedMedia
from app.rag.parsers import parse_document
from app.rag.service import DocumentService
from app.storage.memory import InMemoryRepository
from app.tools.docs import SearchDocsArgs, search_docs
from app.tools.spec import ToolContext


def _service(repo: InMemoryRepository | None = None) -> DocumentService:
    return DocumentService(
        repo or InMemoryRepository(),
        HashEmbedder(dim=128),
        storage_dir=Path("data") / "test-docs",
        ocr=NoopOcr(),
    )


# ---------------------------------------------------------------- 切分


def test_chunk_short_text_single_chunk() -> None:
    assert chunk_text("猫咪今天打了疫苗。") == ["猫咪今天打了疫苗。"]


def test_chunk_long_text_is_split_with_overlap() -> None:
    text = "。".join(f"第{i}段记录了宠物的健康情况" for i in range(60)) + "。"
    chunks = chunk_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 260 for c in chunks)
    # 相邻块必须有重叠字符，否则长句被切断后上下文丢失
    assert chunks[0][-10:] in chunks[1]


def test_chunk_rejects_bad_params() -> None:
    with pytest.raises(ValueError):
        chunk_text("abc", size=0)
    with pytest.raises(ValueError):
        chunk_text("abc", size=100, overlap=100)


# ---------------------------------------------------------------- 嵌入


@pytest.mark.asyncio
async def test_hash_embedder_is_deterministic_and_normalized() -> None:
    embedder = HashEmbedder(dim=64)
    first, second = await embedder.embed(["猫咪对牛奶过敏", "猫咪对牛奶过敏"])
    assert first == second
    assert abs(sum(v * v for v in first) - 1.0) < 1e-6


@pytest.mark.asyncio
async def test_hash_embedder_ranks_related_text_higher() -> None:
    embedder = HashEmbedder(dim=256)
    query, related, unrelated = await embedder.embed(
        ["疫苗记录", "2026-09-01 打了猫三联疫苗", "今天天气不错适合散步"]
    )
    assert cosine(query, related) > cosine(query, unrelated)


def test_openai_embedder_requires_key() -> None:
    from app.rag.embedder import OpenAICompatEmbedder

    with pytest.raises(ValueError):
        OpenAICompatEmbedder(api_key="", base_url="http://x", model="m")


# ---------------------------------------------------------------- 解析分发


@pytest.mark.asyncio
async def test_parse_text_file_keeps_locator() -> None:
    segments = await parse_document(
        name="note.txt", mime="text/plain", data="第一行\n第二行".encode(), ocr=NoopOcr(), media=None
    )
    assert segments[0].locator == "offset=0"
    assert "第二行" in segments[0].text


@pytest.mark.asyncio
async def test_parse_empty_text_is_unsupported() -> None:
    with pytest.raises(UnsupportedMedia):
        await parse_document(name="empty.txt", mime="text/plain", data=b"  \n", ocr=NoopOcr(), media=None)


@pytest.mark.asyncio
async def test_parse_image_without_ocr_is_unsupported_with_reason() -> None:
    with pytest.raises(UnsupportedMedia) as exc:
        await parse_document(name="shot.png", mime="image/png", data=b"\x89PNG", ocr=NoopOcr(), media=None)
    assert "OCR" in str(exc.value)


@pytest.mark.asyncio
async def test_parse_unknown_suffix_is_unsupported() -> None:
    with pytest.raises(UnsupportedMedia):
        await parse_document(name="a.xyz", mime="application/x", data=b"1", ocr=NoopOcr(), media=None)


@pytest.mark.asyncio
async def test_parse_pdf_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class FakeReader:
        def __init__(self, _stream) -> None:
            self.pages = [FakePage("第一页：疫苗记录"), FakePage("   "), FakePage("第三页：体重 4.6kg")]

    fake_module = types.SimpleNamespace(PdfReader=FakeReader)
    monkeypatch.setitem(sys.modules, "pypdf", fake_module)

    segments = await parse_document(name="a.pdf", mime="application/pdf", data=b"%PDF", ocr=NoopOcr(), media=None)
    assert [s.locator for s in segments] == ["page=1", "page=3"]
    assert "4.6kg" in segments[1].text


# ---------------------------------------------------------------- 服务


@pytest.mark.asyncio
async def test_ingest_then_process_makes_document_searchable() -> None:
    service = _service()
    document = await service.ingest(
        user_id="1001", name="疫苗.txt", mime="text/plain",
        data="2026-09-01 打了猫三联疫苗，医生说下次一年后再打。".encode(),
    )
    assert document.status is DocumentStatus.QUEUED
    ready = await service.process(document)
    assert ready.status is DocumentStatus.READY
    assert ready.chunk_count == 1

    hits = await service.search(user_id="1001", query="什么时候打疫苗", top_k=3)
    assert hits
    assert hits[0].document_name == "疫苗.txt"
    assert hits[0].citation()["kind"] == "doc"


@pytest.mark.asyncio
async def test_ingest_same_file_twice_reuses_record() -> None:
    service = _service()
    payload = "同一份文件的重复上传".encode()
    first = await service.ingest(user_id="1001", name="a.txt", mime="text/plain", data=payload)
    second = await service.ingest(user_id="1001", name="a-copy.txt", mime="text/plain", data=payload)
    assert first.id == second.id


@pytest.mark.asyncio
async def test_search_is_isolated_by_user() -> None:
    service = _service()
    mine = await service.ingest(
        user_id="1001", name="mine.txt", mime="text/plain", data="我的猫叫月亮，对牛奶过敏".encode()
    )
    await service.process(mine)
    theirs = await service.ingest(
        user_id="2002", name="theirs.txt", mime="text/plain", data="他的狗叫大壮，对鸡肉过敏".encode()
    )
    await service.process(theirs)

    hits = await service.search(user_id="2002", query="我的猫叫什么", top_k=5)
    assert all(hit.chunk.user_id == "2002" for hit in hits)
    assert not any("月亮" in hit.chunk.content for hit in hits)


@pytest.mark.asyncio
async def test_unsupported_document_records_reason() -> None:
    service = _service()
    document = await service.ingest(
        user_id="1001", name="clip.mp4", mime="video/mp4", data=b"\x00\x01"
    )
    result = await service.process(document)
    assert result.status is DocumentStatus.UNSUPPORTED
    assert result.error and "ffmpeg" in result.error


@pytest.mark.asyncio
async def test_delete_removes_chunks() -> None:
    service = _service()
    document = await service.ingest(
        user_id="1001", name="a.txt", mime="text/plain", data="要删掉的文档内容".encode()
    )
    await service.process(document)
    assert await service.delete("1001", document.id) is True
    assert await service.search(user_id="1001", query="要删掉") == []
    assert await service.get("1001", document.id) is None


@pytest.mark.asyncio
async def test_oversized_upload_rejected() -> None:
    service = DocumentService(
        InMemoryRepository(),
        HashEmbedder(dim=64),
        storage_dir=Path("data") / "test-docs",
        max_bytes=10,
    )
    with pytest.raises(ValueError, match="上限"):
        await service.ingest(user_id="1001", name="big.txt", mime="text/plain", data=b"x" * 11)


# ---------------------------------------------------------------- 工具


@pytest.mark.asyncio
async def test_search_docs_tool_returns_citations() -> None:
    service = _service()
    document = await service.ingest(
        user_id="1001", name="病历.pdf", mime="text/plain", data="诊断：急性肠胃炎，建议禁食 12 小时".encode()
    )
    await service.process(document)
    ctx = ToolContext(user_id="1001", token="t", run_id="r1", backend=None, docs=service)  # type: ignore[arg-type]
    result = await search_docs(SearchDocsArgs(query="肠胃炎怎么办"), ctx)
    assert result["ok"] is True
    assert result["citations"][0]["kind"] == "doc"
    assert "肠胃炎" in result["items"][0]["content"]


@pytest.mark.asyncio
async def test_search_docs_tool_without_service_is_explicit() -> None:
    ctx = ToolContext(user_id="1001", token="t", run_id="r1", backend=None)  # type: ignore[arg-type]
    result = await search_docs(SearchDocsArgs(query="x"), ctx)
    assert result["ok"] is False
    assert result["code"] == "docs_unavailable"


# ---------------------------------------------------------------- HTTP


@pytest.mark.asyncio
async def test_upload_and_search_over_http(client) -> None:
    response = await client.post(
        "/agent/documents",
        headers=AUTH_HEADERS,
        files={"file": ("疫苗本.txt", "2026-09-01 猫三联第一针".encode(), "text/plain")},
        data={"pet_id": "5001"},
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == DocumentStatus.READY
    assert body["chunk_count"] == 1

    listing = await client.get("/agent/documents", headers=AUTH_HEADERS)
    assert listing.json()["total"] == 1

    detail = await client.get(f"/agent/documents/{body['id']}", headers=AUTH_HEADERS)
    assert detail.status_code == 200

    other = await client.get(
        f"/agent/documents/{body['id']}",
        headers={**AUTH_HEADERS, "satoken": "token-2002", "x-user-id": "2002"},
    )
    assert other.status_code == 404

    removed = await client.delete(f"/agent/documents/{body['id']}", headers=AUTH_HEADERS)
    assert removed.json() == {"deleted": True}


@pytest.mark.asyncio
async def test_capabilities_reports_missing_ocr(client) -> None:
    response = await client.get("/agent/documents/capabilities", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["text"]["supported"] is True
    assert body["image"]["supported"] is False
    assert body["image"]["reason"]


@pytest.mark.asyncio
async def test_unauthenticated_upload_is_401(client) -> None:
    response = await client.post(
        "/agent/documents", files={"file": ("a.txt", b"x", "text/plain")}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_embedder_error_marks_document_failed() -> None:
    """嵌入失败不能让文档停在 PARSING：要落 FAILED + 可读原因，便于重传。"""

    class Broken:
        name = "broken"
        dim = 8

        async def embed(self, texts):
            raise EmbedderError("boom")

    service = DocumentService(InMemoryRepository(), Broken(), storage_dir=Path("data") / "test-docs")
    document = await service.ingest(user_id="1001", name="a.txt", mime="text/plain", data=b"hello world")
    result = await service.process(document)
    assert result.status is DocumentStatus.FAILED
    assert result.error and "EmbedderError" in result.error
