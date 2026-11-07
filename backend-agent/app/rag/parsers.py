"""解析：把上传的字节变成「带 locator 的文本段」。

`locator` 是引用的锚点：
- 文本：`offset=<字符偏移>`
- PDF：`page=<页码，从 1 开始>`
- 图片：`page=1`
- 视频：`t=<秒>`
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from .media import FfmpegMedia
from .ocr import OcrEngine, UnsupportedMedia

TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".csv", ".json", ".log", ".yaml", ".yml"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

MAX_PDF_PAGES = 200
MAX_TEXT_CHARS = 400_000


@dataclass
class ParsedSegment:
    locator: str
    text: str


def _decode(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "ignore")


def _parse_pdf(data: bytes) -> list[ParsedSegment]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - 安装缺失
        raise UnsupportedMedia("服务器缺少 PDF 解析依赖（pypdf）") from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # pypdf 对坏文件抛的异常类型不稳定
        raise UnsupportedMedia(f"PDF 无法打开：{exc.__class__.__name__}") from exc

    pages = reader.pages[:MAX_PDF_PAGES]
    segments: list[ParsedSegment] = []
    for index, page in enumerate(pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:  # 单页坏了不拖垮整篇
            text = ""
        if text:
            segments.append(ParsedSegment(f"page={index}", text))
    if not segments:
        raise UnsupportedMedia("PDF 没有可提取的文字（可能是扫描件，需要 OCR）")
    return segments


async def parse_document(
    *,
    name: str,
    mime: str,
    data: bytes,
    ocr: OcrEngine,
    media: FfmpegMedia,
) -> list[ParsedSegment]:
    suffix = Path(name).suffix.lower()
    if suffix in TEXT_SUFFIXES or mime.startswith("text/"):
        text = _decode(data)[:MAX_TEXT_CHARS].strip()
        if not text:
            raise UnsupportedMedia("文件是空的")
        return [ParsedSegment("offset=0", text)]

    if suffix == ".pdf" or mime == "application/pdf":
        return _parse_pdf(data)

    if suffix in IMAGE_SUFFIXES or mime.startswith("image/"):
        if not ocr.available:
            raise UnsupportedMedia("服务器未安装 OCR（tesseract），暂时无法读取图片文字")
        text = (await ocr.recognize(data)).strip()
        if not text:
            raise UnsupportedMedia("图片里没有识别到文字")
        return [ParsedSegment("page=1", text)]

    if suffix in VIDEO_SUFFIXES or mime.startswith("video/"):
        if not media.available:
            raise UnsupportedMedia("服务器未安装 ffmpeg，暂时无法解析视频")
        if not ocr.available:
            raise UnsupportedMedia("服务器未安装 OCR（tesseract），无法读取视频画面文字")
        segments: list[ParsedSegment] = []
        for seconds, frame in await media.extract_frames(data, suffix=suffix or ".mp4"):
            text = (await ocr.recognize(frame)).strip()
            if text:
                segments.append(ParsedSegment(f"t={seconds}s", text))
        if not segments:
            raise UnsupportedMedia("视频画面里没有识别到文字")
        return segments

    raise UnsupportedMedia(f"暂不支持的文件类型：{suffix or mime or '未知'}")
