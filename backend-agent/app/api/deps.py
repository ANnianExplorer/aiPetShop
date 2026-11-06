"""身份解析：token 换用户，绝不信任请求体里的 user_id。

两种模式：
- backend（默认）：拿 `satoken` 调 Java `/auth/current`，用户身份由业务后端的会话决定；
- header（仅 dev/test）：读 `X-User-Id`，方便本地无后端联调，生产环境配置校验会直接拒绝。

缓存按 token 的 SHA-256 前 16 位做键（不落原文），TTL 默认 60s：
既避免每次对话都打一次后端，又能在用户被禁用后一分钟内失效。
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

import httpx

from ..config import Settings
from ..core.errors import Unauthorized
from ..tools.client import BackendClient

_MAX_CACHE = 512


@dataclass(frozen=True)
class Identity:
    user_id: str
    token: str


class IdentityResolver:
    def __init__(self, settings: Settings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http
        self._cache: dict[str, tuple[Identity, float]] = {}

    async def resolve(self, token: str, *, header_user_id: str | None = None) -> Identity:
        if not token:
            raise Unauthorized("缺少登录凭证")
        if self._settings.auth_mode == "header":
            if not header_user_id:
                raise Unauthorized("header 认证模式需要 X-User-Id 请求头")
            return Identity(user_id=header_user_id, token=token)

        key = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached is not None and cached[1] > now:
            return cached[0]

        client = BackendClient(
            self._settings.backend_base_url,
            token,
            self._http,
            timeout_s=self._settings.backend_timeout_s,
        )
        data = await client.get("/auth/current")
        user_id = str((data or {}).get("id") or "")
        if not user_id:
            raise Unauthorized("无法从登录态解析用户身份")

        identity = Identity(user_id=user_id, token=token)
        if len(self._cache) > _MAX_CACHE:
            self._cache.clear()
        self._cache[key] = (identity, now + self._settings.identity_cache_ttl_s)
        return identity
