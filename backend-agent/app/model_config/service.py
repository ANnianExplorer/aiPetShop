"""管理员统一模型配置：读取、保存、测试连接与运行时热切换。

数据流：
1. 管理端 `PUT /agent/admin/model-config` 写入加密后的 key；
2. `ModelConfigService` 立刻用新配置构建 `ChatModel`；
3. 回调 `create_app` 的 `apply_runtime_model` 重建 graph，并 `AgentRunner.reconfigure`；
4. 在途 run 继续持有旧 graph/model，旧 model 延迟到 shutdown 关闭。

未配置数据库行、或行被禁用时，回退到部署级 `PET_AGENT_LLM_*` 环境变量。
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx

from ..config import Settings
from ..core.errors import InvalidRequest, ModelError
from ..llm.base import ChatModel
from .crypto import ConfigCipher, ConfigCipherError
from .store import ModelConfig, ModelConfigStore, ModelConfigStoreError

BuildModel = Callable[[Settings], ChatModel]


class ModelConfigService:
    def __init__(
        self,
        settings: Settings,
        store: ModelConfigStore,
        cipher: ConfigCipher,
        build_model: BuildModel,
    ) -> None:
        self._settings = settings
        self._store = store
        self._cipher = cipher
        self._build_model = build_model
        self._lock = asyncio.Lock()
        self._current: ChatModel | None = None
        self._retired: list[ChatModel] = []
        self._name: str | None = None
        self._source = "none"
        self._last_error: str | None = None
        self._on_change: Callable[[ChatModel | None, str], None] | None = None

    def set_on_change(self, callback: Callable[[ChatModel | None, str], None]) -> None:
        """app 装配完成后注入：把新 model/graph 接到 AgentRunner。"""
        self._on_change = callback

    # ------------------------------------------------------------ 查询
    @property
    def current_model(self) -> ChatModel | None:
        return self._current

    @property
    def runtime_name(self) -> str | None:
        return self._name

    @property
    def runtime_source(self) -> str:
        return self._source

    @property
    def last_error(self) -> str | None:
        return self._last_error

    async def describe(self) -> dict[str, Any]:
        row = await self._safe_get()
        if row is not None:
            masked, error = self._mask_row(row)
            fallback = "none" if self._settings.model_configured is False else "env"
            if row.enabled and not error:
                fallback = "none"
            return {
                "provider": row.provider,
                "base_url": row.base_url,
                "model": row.model,
                "enabled": row.enabled,
                "source": "db",
                "has_api_key": bool(row.api_key_cipher),
                "api_key_masked": masked,
                "updated_by": row.updated_by,
                "update_time": row.update_time,
                "fallback": fallback,
                "runtime_model": self._name,
                "runtime_source": self._source,
                "error": error or self._last_error,
            }
        masked = _mask_key(self._settings.llm_api_key)
        return {
            "provider": "env" if self._settings.llm_api_key else "",
            "base_url": self._settings.llm_base_url,
            "model": self._settings.llm_model,
            "enabled": self._settings.model_configured,
            "source": "env" if self._settings.model_configured else "none",
            "has_api_key": bool(self._settings.llm_api_key),
            "api_key_masked": masked,
            "updated_by": None,
            "update_time": None,
            "fallback": "none",
            "runtime_model": self._name,
            "runtime_source": self._source,
            "error": self._last_error,
        }

    # ------------------------------------------------------------ 启动/应用
    async def bootstrap(self) -> tuple[ChatModel | None, str]:
        try:
            return await self.apply()
        except Exception as exc:
            self._last_error = str(exc)
            return await self._apply_env_fallback()

    async def apply(self) -> tuple[ChatModel | None, str]:
        async with self._lock:
            row = await self._store.get()
            if row is not None and row.enabled:
                try:
                    key = self._cipher.decrypt(row.api_key_cipher)
                    model = self._build_for(row, key)
                    self._last_error = None
                    return self._install(model, "db")
                except (ConfigCipherError, ModelError, InvalidRequest) as exc:
                    self._last_error = str(exc)
            elif row is not None and not row.enabled:
                self._last_error = None
            else:
                self._last_error = None
            return self._apply_env_fallback_locked()

    # ------------------------------------------------------------ 保存
    async def save(
        self,
        *,
        provider: str,
        base_url: str,
        model: str,
        api_key: str,
        enabled: bool,
        updated_by: str | None,
    ) -> dict[str, Any]:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            raise InvalidRequest("base_url 不能为空")
        old = await self._safe_get()
        cipher_text = old.api_key_cipher if old is not None else ""
        if api_key.strip():
            cipher_text = self._cipher.encrypt(api_key.strip())
        if enabled and not cipher_text:
            raise InvalidRequest("启用模型必须提供 API Key；只修改地址/模型时可留空沿用旧 Key")

        candidate_model: ChatModel | None = None
        if enabled:
            candidate = ModelConfig(
                provider=provider.strip(),
                base_url=normalized,
                model=model.strip(),
                api_key_cipher=cipher_text,
                enabled=True,
                updated_by=updated_by,
            )
            try:
                candidate_model = self._build_for(candidate, self._cipher.decrypt(cipher_text))
            except (ConfigCipherError, ModelError) as exc:
                raise InvalidRequest(f"模型配置不可用：{exc}") from exc
        else:
            candidate = ModelConfig(
                provider=provider.strip(),
                base_url=normalized,
                model=model.strip(),
                api_key_cipher=cipher_text,
                enabled=False,
                updated_by=updated_by,
            )

        candidate.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            await self._store.save(candidate)
        except Exception:
            if candidate_model is not None:
                await candidate_model.aclose()
            raise
        self._last_error = None
        if candidate_model is not None:
            self._install(candidate_model, "db")
        else:
            async with self._lock:
                self._apply_env_fallback_locked()
        return await self.describe()

    # ------------------------------------------------------------ 测试连接
    async def test_connection(
        self,
        *,
        provider: str,
        base_url: str,
        model: str,
        api_key: str,
    ) -> dict[str, Any]:
        old = await self._safe_get()
        normalized = (base_url or (old.base_url if old else self._settings.llm_base_url)).strip().rstrip("/")
        model_name = (model or (old.model if old else self._settings.llm_model)).strip()
        key = (api_key or "").strip()
        if not key and old is not None and old.api_key_cipher:
            try:
                key = self._cipher.decrypt(old.api_key_cipher)
            except ConfigCipherError as exc:
                raise InvalidRequest("已保存的 API Key 无法解密，请重新填写") from exc
        if not key:
            key = self._settings.llm_api_key
        if not normalized or not model_name:
            raise InvalidRequest("base_url 与 model 不能为空")
        if not key:
            raise InvalidRequest("请先填写 API Key")

        url = normalized + "/chat/completions"
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                        "stream": False,
                    },
                )
        except httpx.HTTPError as exc:
            raise InvalidRequest(f"模型接口不可达：{type(exc).__name__}") from exc
        elapsed = int((time.perf_counter() - started) * 1000)
        if resp.status_code >= 400:
            body = " ".join(resp.text.split())[:200]
            raise InvalidRequest(f"模型接口返回 {resp.status_code}：{body}")
        try:
            data = resp.json()
        except ValueError as exc:
            raise InvalidRequest("模型接口返回的不是 JSON") from exc
        if not isinstance(data, dict) or not data.get("choices"):
            raise InvalidRequest("模型接口返回缺少 choices 字段")
        return {"ok": True, "latency_ms": elapsed, "model": model_name, "provider": provider}

    # ------------------------------------------------------------ 内部
    async def _safe_get(self) -> ModelConfig | None:
        try:
            return await self._store.get()
        except ModelConfigStoreError:
            raise
        except Exception as exc:
            raise InvalidRequest(f"读取模型配置失败：{exc}") from exc

    def _build_for(self, config: ModelConfig, api_key: str) -> ChatModel:
        settings = self._settings.model_copy(
            update={
                "llm_base_url": config.base_url,
                "llm_model": config.model,
                "llm_api_key": api_key,
            }
        )
        return self._build_model(settings)

    async def _apply_env_fallback(self) -> tuple[ChatModel | None, str]:
        async with self._lock:
            return self._apply_env_fallback_locked()

    def _apply_env_fallback_locked(self) -> tuple[ChatModel | None, str]:
        if not self._settings.model_configured:
            return self._install(None, "none")
        try:
            model = self._build_model(self._settings)
        except ModelError as exc:
            self._last_error = str(exc)
            return self._install(None, "none")
        return self._install(model, "env")

    def _install(self, model: ChatModel | None, source: str) -> tuple[ChatModel | None, str]:
        if self._current is not None and self._current is not model:
            self._retired.append(self._current)
        self._current = model
        self._name = model.name if model is not None else None
        self._source = source
        if self._on_change is not None:
            self._on_change(model, source)
        return model, source

    def _mask_row(self, row: ModelConfig) -> tuple[str, str | None]:
        if not row.api_key_cipher:
            return "", None
        try:
            return _mask_key(self._cipher.decrypt(row.api_key_cipher)), None
        except ConfigCipherError as exc:
            return "", str(exc)

    async def aclose(self) -> None:
        models = [self._current, *self._retired]
        self._current = None
        self._retired.clear()
        for model in models:
            if model is not None:
                with contextlib.suppress(Exception):
                    await model.aclose()
        await self._store.aclose()


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 4:
        return "****"
    return "****" + key[-4:]
