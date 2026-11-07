"""错误分类：每一类都带稳定 `code`，直接映射成 SSE 的 error 事件与 HTTP 状态码。

模型/网络/策略/预算三类要分开——前两者可重试，后者重试只会更糟。
"""

from __future__ import annotations

from typing import Any


class AgentError(Exception):
    """所有可预期错误的基类。不可预期异常由外层收敛为 internal_error。"""

    code: str = "agent_error"
    http_status: int = 500
    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        http_status: int | None = None,
        retryable: bool | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        if retryable is not None:
            self.retryable = retryable
        self.detail = detail or {}

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.detail:
            payload["detail"] = self.detail
        return payload


class InvalidRequest(AgentError):
    code = "invalid_request"
    http_status = 400


class Unauthorized(AgentError):
    code = "unauthorized"
    http_status = 401


class Forbidden(AgentError):
    code = "forbidden"
    http_status = 403


class NotFound(AgentError):
    code = "not_found"
    http_status = 404


class ToolDenied(AgentError):
    """工具不在当前通道的白名单里，或需要人工确认却没走确认流程。"""

    code = "tool_not_allowed"
    http_status = 403


class ToolFailed(AgentError):
    code = "tool_failed"
    http_status = 502
    retryable = True


class BackendError(AgentError):
    """Java 业务后端返回非 0 code 或网络异常。"""

    code = "backend_error"
    http_status = 502
    retryable = True


class ModelError(AgentError):
    code = "model_error"
    http_status = 502
    retryable = True


class ModelNotConfigured(AgentError):
    code = "model_not_configured"
    http_status = 503


class RunTimeout(AgentError):
    code = "run_timeout"
    http_status = 504


class BudgetExceeded(AgentError):
    """超出 hop / 工具调用 / token / 时长预算：不可重试，重试只会继续烧钱。"""

    code = "budget_exceeded"
    http_status = 429


class RateLimited(AgentError):
    """用户级配额耗尽：与 `budget_exceeded` 分开，前端要显示"稍后再试"而不是"出错了"。"""

    code = "rate_limited"
    http_status = 429
    retryable = True

    def __init__(
        self,
        message: str = "请求太频繁，稍后再试",
        *,
        retry_after_s: int = 60,
        scope: str = "chat",
        limit: int = 0,
    ) -> None:
        super().__init__(
            message,
            detail={"retry_after_s": retry_after_s, "scope": scope, "limit": limit},
        )
        self.retry_after_s = max(1, int(retry_after_s))


class CircuitOpen(AgentError):
    """下游连续失败触发熔断：立即失败，别让请求排队等超时。"""

    code = "circuit_open"
    http_status = 503
    retryable = True

    def __init__(
        self,
        message: str = "下游服务暂时不可用，请稍后再试",
        *,
        retry_after_s: int = 30,
        breaker: str = "",
    ) -> None:
        super().__init__(message, detail={"retry_after_s": retry_after_s, "breaker": breaker})
        self.retry_after_s = max(1, int(retry_after_s))


class InvalidArguments(AgentError):
    code = "invalid_arguments"
    http_status = 422
