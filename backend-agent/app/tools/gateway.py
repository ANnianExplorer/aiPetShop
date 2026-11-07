"""工具网关：模型能碰到的**唯一**执行入口。

职责（顺序即防线）：
1. 工具名必须是注册过的；
2. 通道策略：某些工具只对内开放、副作用工具默认不暴露；
3. 每轮 run 的调用次数预算；
4. 参数按 pydantic 模型校验——未声明字段（如伪造 `user_id`）直接拒绝；
5. 副作用工具两段式：没走上层确认就只返回 proposal，不落库；
6. 审计：每次调用写一条 `tool_call_log`（args 只存摘要，不存原文）。
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from ..core.errors import AgentError
from ..core.logging import log_event
from ..domain.models import ToolResult
from .registry import ToolRegistry
from .spec import ToolContext

tool_log = logging.getLogger("agent.tool")


@dataclass(frozen=True)
class ToolPolicy:
    allowed: frozenset[str] | None = None
    channel_denied: Mapping[str, frozenset[str]] = field(default_factory=dict)
    allow_side_effects: bool = False

    def permits(self, name: str, channel: str, *, side_effect: bool) -> tuple[bool, str]:
        if self.allowed is not None and name not in self.allowed:
            return False, "该工具未在当前部署的白名单内"
        if name in self.channel_denied.get(channel, frozenset()):
            return False, f"该工具对 {channel} 通道不可用"
        if side_effect and not self.allow_side_effects:
            return False, "该工具会产生写入副作用，需用户确认后由 S2 的确认流程执行"
        return True, ""


@dataclass(frozen=True)
class ToolAudit:
    run_id: str
    name: str
    ok: bool
    code: str | None
    latency_ms: int
    args_digest: str


Auditor = Callable[[ToolAudit], Awaitable[None]]


class ToolGateway:
    def __init__(
        self,
        registry: ToolRegistry,
        policy: ToolPolicy | None = None,
        auditor: Auditor | None = None,
        *,
        max_calls_per_run: int = 8,
    ) -> None:
        self._registry = registry
        self._policy = policy or ToolPolicy()
        self._auditor = auditor
        self._max_calls = max_calls_per_run
        self._used: dict[str, int] = {}

    # ---------------------------------------------------------------- 视图
    def names_for(self, channel: str) -> tuple[str, ...]:
        out: list[str] = []
        for name in self._registry.names():
            spec = self._registry.get(name)
            if spec is None:
                continue
            ok, _ = self._policy.permits(name, channel, side_effect=spec.side_effect)
            if ok:
                out.append(name)
        return tuple(out)

    def schemas_for(self, channel: str) -> list[dict[str, Any]]:
        return self._registry.schemas(self.names_for(channel))

    def calls_used(self, run_id: str) -> int:
        return self._used.get(run_id, 0)

    def reset_run(self, run_id: str) -> None:
        self._used.pop(run_id, None)

    # ---------------------------------------------------------------- 执行
    async def invoke(
        self,
        name: str,
        raw_args: Mapping[str, Any],
        ctx: ToolContext,
        channel: str = "app",
    ) -> ToolResult:
        started = time.perf_counter()
        spec = self._registry.get(name)
        if spec is None:
            return await self._finish(
                ctx, name, raw_args, started, ToolResult(
                    ok=False, code="unknown_tool", error=f"没有名为 {name} 的工具"
                )
            )

        permitted, reason = self._policy.permits(name, channel, side_effect=spec.side_effect)
        if not permitted:
            return await self._finish(
                ctx, name, raw_args, started,
                ToolResult(ok=False, code="tool_not_allowed", error=reason),
            )

        used = self._used.get(ctx.run_id, 0)
        if used >= self._max_calls:
            return await self._finish(
                ctx, name, raw_args, started,
                ToolResult(
                    ok=False,
                    code="budget_exceeded",
                    error=f"本轮最多调用 {self._max_calls} 次工具，已用尽；请基于已有信息作答",
                ),
            )

        try:
            args = spec.args_model.model_validate(dict(raw_args))
        except ValidationError as exc:
            return await self._finish(
                ctx, name, raw_args, started,
                ToolResult(ok=False, code="invalid_arguments", error=_format_validation(exc)),
            )

        if spec.side_effect and not ctx.auto_commit:
            self._used[ctx.run_id] = used + 1
            return await self._finish(
                ctx, name, raw_args, started,
                ToolResult(
                    ok=False,
                    code="requires_confirmation",
                    payload={"status": "proposed", "tool": name, "preview": _safe_dump(args)},
                    error="写操作需要用户确认后才执行",
                ),
            )

        self._used[ctx.run_id] = used + 1
        try:
            payload = await spec.handler(args, ctx)
            ok = bool(payload.get("ok", True))
            result = ToolResult(
                ok=ok,
                payload=payload,
                code=None if ok else str(payload.get("code") or "tool_failed"),
                error=None if ok else str(payload.get("error") or ""),
            )
        except AgentError as exc:
            result = ToolResult(ok=False, code=exc.code, error=exc.message)
        except Exception as exc:  # 工具内部任何异常都不允许炸掉整轮对话
            result = ToolResult(ok=False, code="tool_failed", error=f"{type(exc).__name__}: {exc}")

        result.latency_ms = int((time.perf_counter() - started) * 1000)
        return await self._finish(ctx, name, raw_args, started, result)

    # ---------------------------------------------------------------- 内部
    async def _finish(
        self,
        ctx: ToolContext,
        name: str,
        raw_args: Mapping[str, Any],
        started: float,
        result: ToolResult,
    ) -> ToolResult:
        if result.latency_ms == 0:
            result.latency_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            tool_log,
            logging.INFO if result.ok else logging.WARNING,
            "tool call",
            tool=name,
            ok=result.ok,
            code=result.code,
            latency_ms=result.latency_ms,
            args_digest=_digest(raw_args),
        )
        if self._auditor is not None:
            audit = ToolAudit(
                run_id=ctx.run_id,
                name=name,
                ok=result.ok,
                code=result.code,
                latency_ms=result.latency_ms,
                args_digest=_digest(raw_args),
            )
            with contextlib.suppress(Exception):
                # 审计失败不能影响主流程；失败原因由 agent.tool 日志记录
                await self._auditor(audit)
        return result


def _format_validation(exc: ValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors()[:3]:
        loc = ".".join(str(p) for p in err.get("loc", ())) or "参数"
        parts.append(f"{loc}: {err.get('msg')}")
    return "参数不合法 —— " + "；".join(parts)


def _safe_dump(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json") if hasattr(model, "model_dump") else {}


def _digest(raw: Mapping[str, Any]) -> str:
    try:
        text = json.dumps(dict(raw), ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        text = str(raw)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
