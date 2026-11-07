"""熔断器：连续失败就快速失败，别让一次下游故障把整条链路拖死。

为什么需要（而不是靠重试）：LLM / Java 后端挂掉时，重试会让每个请求都等满超时，
并发一高就把线程/连接池占满，最后连 `/healthz` 都排不上队。熔断的作用是把
「等 10 秒再失败」变成「立刻失败」，把资源留给还能服务的请求。

状态机（三态，标准实现）::

    closed --失败达阈值--> open --冷却结束--> half_open --探测成功--> closed
                              ^                    |
                              +----探测失败--------+

设计取舍：
- 只做单实例内存计数：多副本共享状态要 Redis，属 P3，本轮不做（见 ADR-0010）。
- `half_open` 只放一个探测请求，避免「恢复瞬间被流量打死」。
- 只把 `Exception` 记成失败：`CancelledError`（客户端断开）不算下游故障，不能误伤熔断。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from .errors import AgentError, CircuitOpen

T = TypeVar("T")

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


def counts_as_failure(exc: BaseException) -> bool:
    """判定异常是否算「下游故障」。

    - 非 AgentError 的异常（网络、解析、未知 bug）算；
    - AgentError 里只有 `retryable=True` 的算（模型 5xx、后端 502、超时）；
    - 401/403/422 这类调用方问题不算，否则一个过期 token 就能把后端熔断掉。
    """
    if isinstance(exc, AgentError):
        return bool(exc.retryable)
    return True


@dataclass(frozen=True)
class BreakerSnapshot:
    """给 `/readyz` 和日志用的只读快照。"""

    name: str
    state: str
    failures: int
    trips: int
    retry_after_s: float | None

    @property
    def healthy(self) -> bool:
        return self.state != OPEN


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        *,
        threshold: int = 5,
        cooldown_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if threshold < 1:
            raise ValueError("threshold 必须 >= 1")
        self._name = name
        self._threshold = threshold
        self._cooldown_s = float(cooldown_s)
        self._clock = clock
        self._state = CLOSED
        self._failures = 0
        self._trips = 0
        self._opened_at: float | None = None
        self._probe_in_flight = False

    # ------------------------------------------------------------------ 读状态
    @property
    def state(self) -> str:
        # 读的时候顺手推进「冷却结束 → half_open」，避免外部漏调 ensure_allowed
        if self._state == OPEN and self._cooled_down():
            self._state = HALF_OPEN
            self._probe_in_flight = False
        return self._state

    def snapshot(self) -> BreakerSnapshot:
        state = self.state
        retry_after = None
        if state == OPEN and self._opened_at is not None:
            retry_after = max(0.0, self._cooldown_s - (self._clock() - self._opened_at))
        return BreakerSnapshot(
            name=self._name,
            state=state,
            failures=self._failures,
            trips=self._trips,
            retry_after_s=retry_after,
        )

    # ------------------------------------------------------------------ 放行判断
    def ensure_allowed(self) -> None:
        """不满足放行条件就抛 `CircuitOpen`；half_open 时抢占唯一探测名额。"""
        state = self.state
        if state == CLOSED:
            return
        if state == HALF_OPEN and not self._probe_in_flight:
            self._probe_in_flight = True
            return
        retry_after = 1
        if state == OPEN and self._opened_at is not None:
            retry_after = max(1, int(self._cooldown_s - (self._clock() - self._opened_at)) + 1)
        raise CircuitOpen(
            f"{self._name} 连续失败已熔断，请稍后再试",
            retry_after_s=retry_after,
            breaker=self._name,
        )

    # ------------------------------------------------------------------ 结果回写
    def record_success(self) -> None:
        self._failures = 0
        self._state = CLOSED
        self._opened_at = None
        self._probe_in_flight = False

    def record_failure(self) -> None:
        if self._state == HALF_OPEN:  # 探测失败：立刻重新打开，冷却重新计时
            self._trip()
            return
        self._failures += 1
        if self._failures >= self._threshold:
            self._trip()

    def release(self) -> None:
        """流式调用被客户端中断（GeneratorExit）：不记成功也不记失败，只释放探测名额。"""
        self._probe_in_flight = False

    async def call(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """包一层：放行判断 → 执行 → 记成功/失败。异常原样抛出，不改语义。

        只有「值得重试的失败」才计数：鉴权失效（401/403）、参数错误这类
        4xx 是调用方问题，把它们算成下游故障会让熔断器替用户背锅。
        """
        self.ensure_allowed()
        try:
            result = await fn(*args, **kwargs)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if counts_as_failure(exc):
                self.record_failure()
            else:
                self.release()
            raise
        self.record_success()
        return result

    # ------------------------------------------------------------------ 内部
    def _cooled_down(self) -> bool:
        if self._opened_at is None:
            return True
        return (self._clock() - self._opened_at) >= self._cooldown_s

    def _trip(self) -> None:
        self._state = OPEN
        self._opened_at = self._clock()
        self._trips += 1
        self._probe_in_flight = False
