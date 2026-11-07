"""OCR 适配器：只在部署环境真的装了 `tesseract` 时可用。

失败要**可解释**：`UnsupportedMedia` 带上给用户看的原因，由上层落成
`status=4` + `error`，而不是抛 500 或者编造内容。
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Protocol


class UnsupportedMedia(Exception):
    """这类媒体当前环境处理不了；消息直接面向用户。"""


class OcrEngine(Protocol):
    name: str
    available: bool

    async def recognize(self, image: bytes) -> str: ...


class TesseractOcr:
    name = "tesseract"

    def __init__(self, *, lang: str = "chi_sim+eng", timeout_s: float = 20.0) -> None:
        self._exe = shutil.which("tesseract")
        self.available = self._exe is not None
        self._lang = lang
        self._timeout = timeout_s

    async def recognize(self, image: bytes) -> str:
        if not self.available:
            raise UnsupportedMedia("服务器未安装 OCR（tesseract），暂时无法读取图片文字")
        with tempfile.TemporaryDirectory(prefix="ocr-") as tmp:
            src = Path(tmp) / "in.png"
            src.write_bytes(image)
            proc = await asyncio.create_subprocess_exec(
                self._exe,
                str(src),
                "stdout",
                "-l",
                self._lang,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                out, err = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
            except TimeoutError as exc:  # pragma: no cover - 依赖外部进程
                proc.kill()
                raise UnsupportedMedia("OCR 超时，请换一张更小的图片") from exc
            if proc.returncode != 0:
                raise UnsupportedMedia(f"OCR 失败：{err.decode('utf-8', 'ignore')[:120]}")
            return out.decode("utf-8", "ignore").strip()


class NoopOcr:
    """没有 OCR 时的占位实现：能力矩阵里显示"不可用"，调用即报原因。"""

    name = "none"
    available = False

    async def recognize(self, image: bytes) -> str:
        raise UnsupportedMedia("服务器未安装 OCR（tesseract），暂时无法读取图片文字")


def detect_ocr() -> OcrEngine:
    engine = TesseractOcr()
    return engine if engine.available else NoopOcr()
