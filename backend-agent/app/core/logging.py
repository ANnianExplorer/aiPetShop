"""结构化日志：单行 JSON，便于容器采集、按 `run_id` 串联、按 `latency_ms` 聚合。

设计约定（ADR-0007）：
1. 日志行本身就是合法 JSON —— 采集端不需要正则解析；
2. 请求级字段（request_id / user_id / run_id）走 contextvars，业务代码不用层层传参；
3. **不记消息原文**：只记 id、长度、耗时、错误码，避免把用户对话写进日志系统。
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# 请求级上下文：由中间件/运行时写入，JsonFormatter 兜底附加到每条日志
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
run_id_var: ContextVar[str] = ContextVar("run_id", default="")

_CONTEXT_VARS: dict[str, ContextVar[str]] = {
    "request_id": request_id_var,
    "user_id": user_id_var,
    "run_id": run_id_var,
}

# 与 LogRecord 内置属性同名会抛 KeyError（logging 用 setattr 写入 extra）
RESERVED_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "asctime",
    }
)


class JsonFormatter(logging.Formatter):
    """把 LogRecord 压成一行 JSON。`extra={"ctx": {...}}` 的字段会被平铺。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        ctx = getattr(record, "ctx", None)
        if isinstance(ctx, dict):
            payload.update({key: value for key, value in ctx.items() if value is not None})
        for key, var in _CONTEXT_VARS.items():
            if key in payload:
                continue
            value = var.get()
            if value:
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """幂等：重复调用不会叠加 handler（测试与多入口都安全）。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # 第三方库默认太吵，只在 warning 以上输出
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def log_event(logger: logging.Logger, level: int, msg: str, **fields: Any) -> None:
    """结构化打点：`log_event(log, logging.INFO, "tool done", tool="search_logs", ok=True)`。"""
    unknown = set(fields) & RESERVED_ATTRS
    if unknown:  # 开发期自检：防止把 extra 写进保留字段导致 logging 抛异常
        raise ValueError(f"日志字段不能与 LogRecord 内置属性重名：{sorted(unknown)}")
    logger.log(level, msg, extra={"ctx": fields})
