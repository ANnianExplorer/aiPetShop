"""切分：按段落 → 句子聚合到目标长度，块间保留重叠。

为什么自己写而不是用 langchain 的 splitter：
- 我们要保留 `locator`（页码/时间戳），第三方 splitter 只返回字符串；
- 目标长度、重叠、最小长度三个参数在这里集中可测；
- 中文句子边界（。！？；）与英文（.!?）都要切，不能只按空格。
"""

from __future__ import annotations

import re

DEFAULT_SIZE = 800
DEFAULT_OVERLAP = 120
MIN_SIZE = 40

_SENTENCE_SPLIT = re.compile(r"(?<=[。！？；!?;\n])")


def _sentences(text: str) -> list[str]:
    parts: list[str] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        parts.extend(p.strip() for p in _SENTENCE_SPLIT.split(block) if p.strip())
    return parts


def chunk_text(
    text: str,
    *,
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """把长文本切成交叠的块；空文本返回空列表。"""
    if size <= 0:
        raise ValueError("size 必须为正数")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap 必须满足 0 <= overlap < size")

    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    pieces = _sentences(text)
    if not pieces:
        pieces = [text]

    chunks: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for piece in pieces:
        # 单句超长（无标点的长表格）直接硬切
        while len(piece) > size:
            head, piece = piece[:size], piece[size:]
            if buf:
                chunks.append("".join(buf))
                buf, buf_len = [], 0
            chunks.append(head)
        if buf_len + len(piece) > size and buf:
            chunks.append("".join(buf))
            tail = "".join(buf)[-overlap:] if overlap else ""
            buf = [tail] if tail else []
            buf_len = len(tail)
        buf.append(piece)
        buf_len += len(piece)
    if buf:
        joined = "".join(buf).strip()
        if joined:
            chunks.append(joined)

    # 去掉因为重叠产生的过短尾块
    return [c for c in chunks if len(c.strip()) >= MIN_SIZE] or chunks
