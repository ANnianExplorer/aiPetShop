"""Java 业务后端客户端：工具的取数出口。

约定（已与现有 controller 核对）：
- 统一返回 `{"code":0,"data":...}`，非 0 即业务错误；
- 鉴权走 `satoken` 请求头（与前端一致），Agent 不持有任何独立身份；
- 只读请求可重试，写请求不重试（避免重复写入）。
"""

from __future__ import annotations

from typing import Any

import httpx

from ..core.errors import BackendError, Unauthorized

AUTH_FAILED_CODE = 40100
RATE_LIMITED_CODE = 42900


class BackendClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        http: httpx.AsyncClient,
        *,
        timeout_s: float = 8.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._http = http
        self._timeout = timeout_s

    @property
    def base_url(self) -> str:
        return self._base

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=payload or {})

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self._base + path
        headers = {"satoken": self._token, "Accept": "application/json"}
        try:
            resp = await self._http.request(
                method, url, headers=headers, timeout=self._timeout, **kwargs
            )
        except httpx.TimeoutException as exc:
            raise BackendError(f"业务后端超时：{path}") from exc
        except httpx.TransportError as exc:
            raise BackendError(f"业务后端不可达：{path}（{type(exc).__name__}）") from exc

        if resp.status_code in (401, 403):
            raise Unauthorized("登录态失效，请重新登录")
        if resp.status_code >= 400:
            raise BackendError(
                f"业务后端 {resp.status_code}：{path}",
                detail={"status": resp.status_code, "body": resp.text[:300]},
            )

        try:
            body = resp.json()
        except ValueError as exc:
            raise BackendError(f"业务后端返回非 JSON：{path}") from exc

        code = body.get("code")
        if code == 0:
            return body.get("data")
        message = str(body.get("message") or "业务后端返回异常")
        if code == AUTH_FAILED_CODE:
            raise Unauthorized(message)
        if code == RATE_LIMITED_CODE:
            raise BackendError(f"业务后端限流：{message}")
        raise BackendError(message, detail={"code": code, "path": path})
