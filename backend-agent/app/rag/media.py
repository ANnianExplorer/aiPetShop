"""视频抽帧：依赖外部 `ffmpeg` 二进制（Python 包不带）。

抽出来的帧交给 OCR；没有 OCR/ffmpeg 时整条链路给出明确原因，
避免"上传成功但什么都搜不到"的假成功。
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from .ocr import UnsupportedMedia

DEFAULT_INTERVAL_S = 15
MAX_FRAMES = 40


class FfmpegMedia:
    name = "ffmpeg"

    def __init__(self, *, interval_s: int = DEFAULT_INTERVAL_S, timeout_s: float = 60.0) -> None:
        self._exe = shutil.which("ffmpeg")
        self.available = self._exe is not None
        self.interval_s = interval_s
        self._timeout = timeout_s

    async def extract_frames(self, video: bytes, *, suffix: str = ".mp4") -> list[tuple[int, bytes]]:
        if not self.available:
            raise UnsupportedMedia("服务器未安装 ffmpeg，暂时无法解析视频")
        with tempfile.TemporaryDirectory(prefix="video-") as tmp:
            root = Path(tmp)
            src = root / f"input{suffix}"
            src.write_bytes(video)
            pattern = root / "frame-%03d.jpg"
            proc = await asyncio.create_subprocess_exec(
                self._exe,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(src),
                "-vf",
                f"fps=1/{self.interval_s}",
                "-frames:v",
                str(MAX_FRAMES),
                "-q:v",
                "3",
                str(pattern),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                _, err = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
            except TimeoutError as exc:  # pragma: no cover - 依赖外部进程
                proc.kill()
                raise UnsupportedMedia("视频抽帧超时，请换更短的视频") from exc
            if proc.returncode != 0:
                raise UnsupportedMedia(f"视频解析失败：{err.decode('utf-8', 'ignore')[:120]}")
            frames: list[tuple[int, bytes]] = []
            for index, path in enumerate(sorted(root.glob("frame-*.jpg"))):
                frames.append((index * self.interval_s, path.read_bytes()))
            return frames


def detect_media() -> FfmpegMedia:
    return FfmpegMedia()
