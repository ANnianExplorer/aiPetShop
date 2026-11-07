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

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "key": self.key,
            "payload": dict(self.payload),
            "attempt": self.attempt,
        }

    @classmethod
    def from_json(cls, raw: Mapping[str, Any]) -> TaskMessage:
        return cls(
            id=str(raw["id"]),
            topic=str(raw["topic"]),
            key=str(raw["key"]),
            payload=dict(raw.get("payload") or {}),
            attempt=int(raw.get("attempt", 1)),
        )


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

    async def recover(self, topics: Sequence[str] | None = None) -> int:
        """把崩溃时卡在「在途」里的消息搬回待消费队列，返回条数。

        进程启动时调用一次：上次异常退出时 `receive` 过但没 `ack` 的消息，
        否则会永远躺在 processing 里。内存实现没有在途态，返回 0。
        """

    async def replay_dead_letter(self, topic: str, *, limit: int = 10) -> int:
        """把死信搬回队列重试，`attempt` 重置为 1；返回搬了几条。

        死信不是垃圾桶：修好下游（或补完数据）之后要能把它们放回来。
        """

    async def aclose(self) -> None: ...


def make_message(topic: str, key: str, payload: Mapping[str, Any]) -> TaskMessage:
    return TaskMessage(id=new_id(), topic=topic, key=key, payload=dict(payload), attempt=1)
