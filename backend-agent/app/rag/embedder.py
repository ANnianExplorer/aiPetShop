"""嵌入：默认本地哈希嵌入，可选 OpenAI 兼容接口。

为什么默认不是"调模型"：
- 离线/没配 key 的环境也要能上传、能检索，否则上传即失败；
- 哈希嵌入（char n-gram → signed hashing）确定性、零成本、可单测；
- 语义能力弱是已知代价，换 `openai` 后端即可，接口不变（`dim` 会标出旧向量）。
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

import httpx

_TOKEN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


class EmbedderError(RuntimeError):
    """嵌入失败（网络/上游返回异常），由上层转成业务错误，不吞掉。"""


class Embedder(Protocol):
    name: str
    dim: int

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def _l2(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


class HashEmbedder:
    """字符 3-gram + 词元的有符号哈希；同一文本永远得到同一向量。"""

    name = "hash"

    def __init__(self, dim: int = 256) -> None:
        if dim < 32:
            raise ValueError("dim 太小，至少 32")
        self.dim = dim

    def _grams(self, text: str) -> list[str]:
        lowered = text.lower()
        tokens = _TOKEN.findall(lowered)
        grams: list[str] = []
        for token in tokens:
            grams.append(token)
            if len(token) >= 3:
                grams.extend(token[i : i + 3] for i in range(len(token) - 2))
        # 中文逐字 + 相邻二字，保证短句也有信号
        han = [t for t in tokens if "\u4e00" <= t <= "\u9fff"]
        grams.extend(han[i] + han[i + 1] for i in range(len(han) - 1))
        return grams or [lowered]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for gram in self._grams(text):
            digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
            h = int.from_bytes(digest, "big")
            sign = 1.0 if h & 1 else -1.0
            vec[h % self.dim] += sign
        return _l2(vec)

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]


class OpenAICompatEmbedder:
    """`POST {base_url}/embeddings`，兼容 OpenAI / 大多数自建服务。"""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        dim: int = 1024,
        client: httpx.AsyncClient | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        if not api_key:
            raise ValueError("openai 嵌入后端必须提供 api_key")
        self._key = api_key
        self._base = base_url.rstrip("/")
        self._model = model
        self.dim = dim
        self._client = client
        self._timeout = timeout_s

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        own = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            resp = await client.post(
                f"{self._base}/embeddings",
                headers={"Authorization": f"Bearer {self._key}"},
                json={"model": self._model, "input": list(texts)},
            )
            if resp.status_code >= 400:
                raise EmbedderError(f"嵌入接口返回 {resp.status_code}")
            payload = resp.json()
            data = payload.get("data") or []
            vectors = [_l2([float(x) for x in item.get("embedding", [])]) for item in data]
            if len(vectors) != len(texts):
                raise EmbedderError("嵌入条数与输入不一致")
            if vectors and vectors[0]:
                self.dim = len(vectors[0])
            return vectors
        except httpx.HTTPError as exc:  # 网络层单独归类
            raise EmbedderError(f"嵌入请求失败：{exc.__class__.__name__}") from exc
        finally:
            if own:
                await client.aclose()


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    return dot  # 两端都已 L2 归一化


def build_embedder(settings) -> Embedder:
    backend = getattr(settings, "embed_backend", "hash")
    if backend == "openai":
        return OpenAICompatEmbedder(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=getattr(settings, "embed_model", "text-embedding-3-small"),
            dim=getattr(settings, "embed_dim", 1024),
        )
    return HashEmbedder(dim=getattr(settings, "embed_dim", 256))
