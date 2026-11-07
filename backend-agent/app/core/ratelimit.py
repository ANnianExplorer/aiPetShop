"""用户级配额：滑动窗口（分钟）+ 自然日总额。

三个设计取舍：
1. 失败开放（fail-open）：配额服务自己挂了，不应该让所有用户都聊不了天——记日志、放行；
2. 时间窗用「事件时间戳」而不是「初始窗口」，避免 23:59 与 00:00 各打一轮双倍配额；
3. 内存实现与 Redis 实现语义对齐（同样的 limit / remaining / retry_after），
   测试用同一套断言跑两遍，只有 Redis 版才真正跨进程。
"""

from __future__ import annotations

import contextlib
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Protocol

from ..core.logging import log_event

rate_log = logging.getLogger("agent.ratelimit")


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    scope: str
    limit: int
    remaining: int
    retry_after_s: int = 0


class RateLimiter(Protocol):
    async def hit(self, user_id: str, scope: str = "chat") -> LimitDecision: ...

    async def aclose(self) -> None: ...


class InMemoryRateLimiter:
    """单进程实现：够单副本部署与测试用，多副本必须换成 Redis 版。"""

    def __init__(
        self,
        per_minute: int,
        per_day: int,
        *,
        clock: Any = time.time,
    ) -> None:
        self._per_minute = per_minute
        self._per_day = per_day
        self._clock = clock
        self._hits: dict[tuple[str, str], deque[float]] = {}

    async def hit(self, user_id: str, scope: str = "chat") -> LimitDecision:
        now = float(self._clock())
        bucket = self._hits.setdefault((scope, user_id), deque())
        _prune(bucket, now - 86400.0)

        in_minute = sum(1 for ts in bucket if ts > now - 60.0)
        if in_minute >= self._per_minute:
            oldest = next(ts for ts in bucket if ts > now - 60.0)
            return LimitDecision(
                allowed=False,
                scope=scope,
                limit=self._per_minute,
                remaining=0,
                retry_after_s=max(1, int(60 - (now - oldest)) + 1),
            )
        if len(bucket) >= self._per_day:
            return LimitDecision(
                allowed=False,
                scope=scope,
                limit=self._per_day,
                remaining=0,
                retry_after_s=60,
            )

        bucket.append(now)
        return LimitDecision(
            allowed=True,
            scope=scope,
            limit=self._per_minute,
            remaining=max(0, self._per_minute - in_minute - 1),
        )

    async def aclose(self) -> None:
        self._hits.clear()


class RedisRateLimiter:
    """多副本实现：`INCR` + `EXPIRE` 两个计数键，键本身带窗口后缀，天然过期。"""

    def __init__(self, client: Any, per_minute: int, per_day: int) -> None:
        self._client = client
        self._per_minute = per_minute
        self._per_day = per_day

    async def hit(self, user_id: str, scope: str = "chat") -> LimitDecision:
        now = int(time.time())
        minute_key = f"agent:rl:{scope}:{user_id}:m:{now // 60}"
        day_key = f"agent:rl:{scope}:{user_id}:d:{now // 86400}"
        try:
            pipe = self._client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)
            pipe.incr(day_key)
            pipe.expire(day_key, 90000)
            minute_count, _, day_count, _ = await pipe.execute()
        except Exception as exc:  # 配额设施故障不能变成全站不可用
            log_event(rate_log, logging.WARNING, "rate limiter unavailable", error=type(exc).__name__)
            return LimitDecision(
                allowed=True, scope=scope, limit=self._per_minute, remaining=self._per_minute
            )

        minute_count = int(minute_count)
        day_count = int(day_count)
        if minute_count > self._per_minute:
            return LimitDecision(
                allowed=False,
                scope=scope,
                limit=self._per_minute,
                remaining=0,
                retry_after_s=max(1, 60 - now % 60),
            )
        if day_count > self._per_day:
            return LimitDecision(
                allowed=False,
                scope=scope,
                limit=self._per_day,
                remaining=0,
                retry_after_s=max(1, 86400 - now % 86400),
            )
        return LimitDecision(
            allowed=True,
            scope=scope,
            limit=self._per_minute,
            remaining=max(0, self._per_minute - minute_count),
        )

    async def aclose(self) -> None:
        client = self._client
        closer = getattr(client, "aclose", None) or getattr(client, "close", None)
        if closer is not None:
            with contextlib.suppress(Exception):
                await closer()


def _prune(bucket: deque[float], deadline: float) -> None:
    while bucket and bucket[0] <= deadline:
        bucket.popleft()


def create_rate_limiter(settings: Any) -> RateLimiter:
    if settings.rate_limit_backend == "redis":
        from .redis_client import create_redis

        client = create_redis(settings.redis_url)
        return RedisRateLimiter(client, settings.rate_limit_per_minute, settings.rate_limit_per_day)
    return InMemoryRateLimiter(settings.rate_limit_per_minute, settings.rate_limit_per_day)
