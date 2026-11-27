"""任务队列契约（at-least-once）。

为什么要有这层抽象：请求路径上的旁路工作（记忆抽取、审计落库）不该拖慢首字，
但也不该依赖某一个中间件。上层只认这份协议，实现可以是进程内、Redis 列表，
将来换成 RocketMQ 也不动业务代码（见 ADR-0009）。

三条硬约定：
1. **at-least-once**：`receive` 可能拿到重复消息，消费端必须自己幂等；
2. **ack/nack 必须配对**：拿到消息就要 ack（成功）或 nack（失败），否则
   Redis 实现里那条消息会一直躺在 processing 列表里；
3. **publish 不阻塞**：队列满时抛 `TaskQueueFull`，调用方降级为同步执行，
   宁可慢一点，也不把对话卡死。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ..core.ids import new_id


class TaskQueueFull(Exception):
    """队列满或中间件不可用。调用方应降级为同步执行。"""


class TaskQueueError(Exception):
    """底层存储故障。与 `TaskQueueFull` 分开，便于只对前者做降级。"""


@dataclass(frozen=True)
class TaskMessage:
    id: str
    topic: str
    key: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    attempt: int = 1
    redrives: int = 0

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "key": self.key,
            "payload": dict(self.payload),
            "attempt": self.attempt,
            "redrives": self.redrives,
        }

    @classmethod
    def from_json(cls, raw: Mapping[str, Any]) -> TaskMessage:
        return cls(
            id=str(raw["id"]),
            topic=str(raw["topic"]),
            key=str(raw["key"]),
            payload=dict(raw.get("payload") or {}),
            attempt=int(raw.get("attempt", 1)),
            redrives=int(raw.get("redrives", 0)),
        )

    def reborn(self, *, attempt: int, redrives: int | None = None) -> TaskMessage:
        """同一条消息换个计数再来一次（保留 id/key/payload）。"""
        return TaskMessage(
            id=self.id,
            topic=self.topic,
            key=self.key,
            payload=self.payload,
            attempt=attempt,
            redrives=self.redrives if redrives is None else redrives,
        )


def backoff_seconds(attempt: int, *, base: float = 5.0, cap: float = 600.0) -> float:
    """指数退避：base * 2^(attempt-1)，封顶 cap。

    失败一次就立刻重投会让下游抖动变成热循环；退避把重试摊开到分钟级。
    """
    base = max(0.0, float(base))
    cap = max(0.0, float(cap))
    if base == 0 or cap == 0:
        return 0.0
    exponent = max(0, int(attempt) - 1)
    # 指数可能很大，先夹住指数避免溢出
    return min(cap, base * float(2 ** min(exponent, 30)))


TaskHandler = Callable[[TaskMessage], Awaitable[None]]


@runtime_checkable
class TaskQueue(Protocol):
    async def publish(self, topic: str, key: str, payload: Mapping[str, Any]) -> str:
        """投递一条消息，返回消息 id（19 位，可直接当去重键/主键）。"""

    async def receive(self, topic: str, timeout_s: float = 1.0) -> TaskMessage | None:
        """取一条消息；超时返回 None。取到后必须 ack 或 nack。"""

    async def ack(self, message: TaskMessage) -> None: ...

    async def nack(self, message: TaskMessage, *, error: str) -> None:
        """失败重投；超过最大次数进死信。"""

    async def depth(self, topic: str) -> int: ...

    async def dead_letters(self, topic: str) -> list[TaskMessage]:
        """死信列表（验收/排障用），两种后端同签名。"""

    async def dead_letter_count(self, topic: str) -> int:
        """死信条数（运维/告警用），必须包含无法解析的坏消息。

        `dead_letters()` 会把坏 payload 跳过以免展示层崩溃；但告警不能跟着漏，
        否则会变成「页面显示 0 条、实际卡着一条永远重放不了的消息」。
        Redis 实现用 `LLEN`（O(1)），内存实现用列表长度。
        """

    async def recover(self, topics: Sequence[str] | None = None) -> int:
        """把崩溃时卡在「在途」里的消息搬回待消费队列，返回条数。

        进程启动时调用一次：上次异常退出时 `receive` 过但没 `ack` 的消息，
        否则会永远躺在 processing 里。内存实现没有在途态，返回 0。
        """

    async def replay_dead_letter(self, topic: str, *, limit: int = 10) -> int:
        """把死信搬回队列重试，`attempt` 重置为 1；返回搬了几条。

        死信不是垃圾桶：修好下游（或补完数据）之后要能把它们放回来。
        """

    async def sweep(self, topics: Sequence[str], *, older_than_s: float) -> int:
        """把「取走太久还没 ack」的在途消息搬回待消费队列，返回条数。

        语义对齐 SQS visibility timeout：超过 `older_than_s` 仍停在在途里的消息
        视为消费者已死，搬回主队列并把 `attempt + 1`（防止「一取就崩」死循环）。
        代价是慢任务可能被执行两次——消费端必须幂等（ADR-0009 第 4 条）。
        内存实现没有跨进程在途态，返回 0，不假装能扫。
        """

    async def retry_due(self, topics: Sequence[str], *, now: float | None = None) -> int:
        """把退避到期的重试消息搬回待消费队列，返回条数（B4）。

        `nack` 不会立刻回主队列，而是写进 `:retry`（ZSET，score 为到期时间）；
        巡检器周期性调用本方法把它们放回。测试可注入 `now` 免等待。
        """

    async def redrive_dead_letters(
        self, topics: Sequence[str], *, limit_per_topic: int, max_redrives: int
    ) -> int:
        """自动重投死信（有界）：`redrives + 1`，达上限的留在死信等人处理。

        默认不开启——死信通常意味着代码/数据问题，自动重投只会刷日志。
        """

    async def aclose(self) -> None: ...


def make_message(topic: str, key: str, payload: Mapping[str, Any]) -> TaskMessage:
    return TaskMessage(id=new_id(), topic=topic, key=key, payload=dict(payload), attempt=1)
