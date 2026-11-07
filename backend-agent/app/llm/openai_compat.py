"""OpenAI 兼容实现（DeepSeek / 通义 / vLLM / Ollama 都走这套）。

比「能跑就行」多做的四件事：
1. 重试：只对 429/5xx/超时重试，指数退避 + 尊重 `Retry-After`；
2. 用量：流式请求带 `stream_options.include_usage`，拿不到就降级为 0（不阻塞回答）；
3. 参数：工具参数 JSON 解析失败不抛给运行时，而是标记 `parse_error` 交回网关，
   让模型看到「你参数写错了」并自我修正，而不是整轮 run 失败；
4. 错误：统一收敛成 `ModelError`，`retryable` 标明是否值得重试。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from ..config import Settings
from ..core.errors import ModelError
from ..domain.models import Usage
from .base import ChatModel, LLMReply, StreamChunk, ToolCall

_RETRY_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})


class OpenAICompatModel(ChatModel):
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        if not settings.llm_api_key:
            raise ModelError("PET_AGENT_LLM_API_KEY 未配置", code="model_not_configured", http_status=503)
        self._settings = settings
        self._url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.llm_timeout_s, connect=10.0),
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        )

    @property
    def name(self) -> str:
        return self._settings.llm_model

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # ------------------------------------------------------------------ 非流式
    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> LLMReply:
        payload: dict[str, Any] = {
            "model": self._settings.llm_model,
            "messages": messages,
            "temperature": self._settings.llm_temperature,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        data = await self._post_json(payload)
        try:
            message = (data.get("choices") or [{}])[0].get("message") or {}
        except (AttributeError, IndexError) as exc:  # 结构异常：明确报错，别静默返回空
            raise ModelError(f"模型返回结构异常：{exc}") from exc

        calls: list[ToolCall] = []
        for raw in message.get("tool_calls") or []:
            fn = raw.get("function") or {}
            raw_args = fn.get("arguments") or "{}"
            args: dict[str, Any] = {}
            parse_error: str | None = None
            try:
                parsed = json.loads(raw_args)
                if isinstance(parsed, dict):
                    args = parsed
                else:
                    parse_error = "参数必须是 JSON 对象"
            except json.JSONDecodeError as exc:
                parse_error = f"JSON 解析失败：{exc.msg}"
            calls.append(
                ToolCall(
                    id=str(raw.get("id") or ""),
                    name=str(fn.get("name") or ""),
                    arguments=args,
                    raw_arguments=raw_args,
                    parse_error=parse_error,
                )
            )

        usage = data.get("usage") or {}
        return LLMReply(
            text=message.get("content") or "",
            tool_calls=calls,
            usage=Usage(
                int(usage.get("prompt_tokens") or 0),
                int(usage.get("completion_tokens") or 0),
            ),
        )

    # ------------------------------------------------------------------ 流式
    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[StreamChunk]:
        payload: dict[str, Any] = {
            "model": self._settings.llm_model,
            "messages": messages,
            "temperature": self._settings.llm_temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        try:
            async for chunk in self._stream_once(payload):
                yield chunk
        except ModelError as exc:
            # 个别兼容端点不认 stream_options：去掉再试一次（仅一次，不无限重试）
            if "stream_options" in str(exc.detail.get("body", "")) or exc.detail.get("status") == 400:
                payload.pop("stream_options", None)
                async for chunk in self._stream_once(payload):
                    yield chunk
            else:
                raise

    async def _stream_once(self, payload: dict[str, Any]) -> AsyncIterator[StreamChunk]:
        attempts = self._settings.llm_max_retries + 1
        for attempt in range(attempts):
            try:
                async with self._client.stream("POST", self._url, json=payload) as resp:
                    if resp.status_code in _RETRY_STATUS and attempt + 1 < attempts:
                        await resp.aread()
                        raise _Retry(resp.status_code, resp.headers.get("retry-after"))
                    if resp.status_code >= 400:
                        body = (await resp.aread()).decode("utf-8", "replace")[:500]
                        raise ModelError(
                            f"模型接口 {resp.status_code}",
                            detail={"status": resp.status_code, "body": body},
                        )
                    async for line in resp.aiter_lines():
                        chunk = _parse_sse_line(line)
                        if chunk is not None:
                            yield chunk
                    return
            except _Retry as exc:
                await asyncio.sleep(_backoff(attempt, exc.retry_after))
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt + 1 >= attempts:
                    raise ModelError(f"模型接口不可达：{exc}") from exc
                await asyncio.sleep(_backoff(attempt, None))
        raise ModelError("模型接口重试次数用尽")

    # ------------------------------------------------------------------ 内部
    async def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        attempts = self._settings.llm_max_retries + 1
        last: Exception | None = None
        for attempt in range(attempts):
            try:
                resp = await self._client.post(self._url, json=payload)
                if resp.status_code in _RETRY_STATUS and attempt + 1 < attempts:
                    last = ModelError(f"模型接口 {resp.status_code}")
                    await asyncio.sleep(_backoff(attempt, resp.headers.get("retry-after")))
                    continue
                if resp.status_code >= 400:
                    raise ModelError(
                        f"模型接口 {resp.status_code}",
                        detail={"status": resp.status_code, "body": resp.text[:500]},
                    )
                return resp.json()
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last = exc
                if attempt + 1 >= attempts:
                    raise ModelError(f"模型接口不可达：{exc}") from exc
                await asyncio.sleep(_backoff(attempt, None))
        raise ModelError(f"模型接口失败：{last}")


class _Retry(Exception):
    def __init__(self, status: int, retry_after: str | None) -> None:
        self.retry_after = retry_after
        super().__init__(f"retry {status}")


def _backoff(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return min(float(retry_after), 5.0)
        except ValueError:
            pass
    return min(0.4 * (2**attempt), 4.0)


def _parse_sse_line(line: str) -> StreamChunk | None:
    if not line.startswith("data:"):
        return None
    raw = line[5:].strip()
    if not raw or raw == "[DONE]":
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    usage = obj.get("usage")
    if usage:
        return StreamChunk(
            usage=Usage(
                int(usage.get("prompt_tokens") or 0),
                int(usage.get("completion_tokens") or 0),
            )
        )
    delta = (obj.get("choices") or [{}])[0].get("delta") or {}
    text = delta.get("content")
    return StreamChunk(text=text) if text else None


def build_model(settings: Settings, client: httpx.AsyncClient | None = None) -> ChatModel:
    return OpenAICompatModel(settings, client)
