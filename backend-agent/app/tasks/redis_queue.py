"""Redis 列表实现：`LPUSH` 投递 + `BRPOPLPUSH` 取用 + processing 列表保底。

只用了 Redis 5.0 就有的命令（`LPUSH` / `RPOPLPUSH` / `LREM` / `LLEN` / `LRANGE`），
**没有**用 Stream consumer group——那套语义本项目只需要一进一出，
列表够用，而且测试里能用一个极小的 FakeRedis 覆盖。

崩溃语义（at-least-once）：消息取走后放进 `:processing`，ack 才删。
进程崩了，下一次消费把 processing 里的残留搬回主列表（`recover_inflight`），
代价是可能重复投递一次——消费端按 key 幂等，见 ADR-0009 第 4 条。
"""

from __future__ import annotations

import contextlib
import json
import logging
import time
from collections.abc import Awaitable, Mapping, Sequence
from typing import Any, Protocol

from ..core.logging import log_event
from .base import TaskMessage, TaskQueueFull, make_message

task_log = logging.getLogger("agent.task")

_DLQ_SUFFIX = ":dlq"
_PROCESSING_SUFFIX = ":processing"
_CLAIMED_SUFFIX = ":claimed"


class RedisLike(Protocol):
    """只声明用到的命令，方便测试注入 FakeRedis。"""

    async def lpush(self, key: str, *values: str) -> int: ...
    async def rpoplpush(self, src: str, dst: str) -> str | None: ...
    async def brpoplpush(self, src: str, dst: str, timeout: int) -> str | None: ...
    async def lrem(self, key: str, count: int, value: str) -> int: ...
    async def llen(self, key: str) -> int: ...
    async def lrange(self, key: str, start: int, end: int) -> list[str]: ...
    async def zadd(self, key: str, mapping: Mapping[str, float]) -> int: ...
    async def zrem(self, key: str, *values: str) -> int: ...
    async def zrangebyscore(self, key: str, min: float, max: float) -> list[str]: ...
    async def aclose(self) -> None: ...


class RedisTaskQueue:
    def __init__(
        self,
        client: RedisLike,
        *,
        prefix: str = "pet:task",
        max_attempts: int = 3,
        block_timeout_s: int = 1,
    ) -> None:
        self._redis = client
        self._prefix = prefix
        self._max_attempts = max_attempts
        self._block_timeout = max(1, int(block_timeout_s))

    # ------------------------------------------------------------------ key
    def _topic_key(self, topic: str) -> str:
        return f"{self._prefix}:{topic}"

    def _processing_key(self, topic: str) -> str:
        return f"{self._topic_key(topic)}{_PROCESSING_SUFFIX}"

    def _dlq_key(self, topic: str) -> str:
        return f"{self._topic_key(topic)}{_DLQ_SUFFIX}"

    def _claimed_key(self, topic: str) -> str:
        return f"{self._topic_key(topic)}{_CLAIMED_SUFFIX}"

    # -------------------------------------------------------------- publish
    async def publish(self, topic: str, key: str, payload: Mapping[str, Any]) -> str:
        message = make_message(topic, key, payload)
        try:
            await self._redis.lpush(self._topic_key(topic), json.dumps(message.to_json(), ensure_ascii=False))
        except Exception as exc:  # 中间件故障：让调用方降级为同步执行
            raise TaskQueueFull(f"Redis 任务队列不可用：{exc}") from exc
        return message.id

    # -------------------------------------------------------------- consume
    async def receive(self, topic: str, timeout_s: float = 1.0) -> TaskMessage | None:
        raw = await self._redis.brpoplpush(
            self._topic_key(topic), self._processing_key(topic), self._block_timeout
        )
        if raw is None:
            return None
        try:
            message = TaskMessage.from_json(json.loads(raw))
        except (ValueError, KeyError, TypeError) as exc:
            # 坏消息不能卡住队列：直接进死信并返回 None
            await self._redis.lpush(self._dlq_key(topic), raw)
            log_event(task_log, logging.ERROR, "task payload invalid", topic=topic, error=str(exc))
            return None
        # 登记取用时刻：巡检据此判断「这条是不是被取走后死在半路」
        await self._redis.zadd(self._claimed_key(topic), {raw: time.time()})
        return message

    async def ack(self, message: TaskMessage) -> None:
        raw = json.dumps(message.to_json(), ensure_ascii=False)
        await self._redis.lrem(self._processing_key(message.topic), 1, raw)
        await self._redis.zrem(self._claimed_key(message.topic), raw)

    async def nack(self, message: TaskMessage, *, error: str) -> None:
        raw = json.dumps(message.to_json(), ensure_ascii=False)
        await self._redis.lrem(self._processing_key(message.topic), 1, raw)
        await self._redis.zrem(self._claimed_key(message.topic), raw)
        if message.attempt >= self._max_attempts:
            await self._redis.lpush(self._dlq_key(message.topic), raw)
            log_event(task_log, logging.ERROR, "task dead letter", topic=message.topic,
                      key=message.key, attempts=message.attempt, error=error)
            return
        retried = TaskMessage(
            id=message.id,
            topic=message.topic,
            key=message.key,
            payload=message.payload,
            attempt=message.attempt + 1,
        )
        await self._redis.lpush(
            self._topic_key(message.topic), json.dumps(retried.to_json(), ensure_ascii=False)
        )

    async def depth(self, topic: str) -> int:
        return int(await self._redis.llen(self._topic_key(topic)))

    async def dead_letters(self, topic: str) -> list[TaskMessage]:
        raws = await self._redis.lrange(self._dlq_key(topic), 0, -1)
        out: list[TaskMessage] = []
        for raw in raws:
            with contextlib.suppress(ValueError, KeyError, TypeError):
                out.append(TaskMessage.from_json(json.loads(raw)))
        return out

    async def recover_inflight(self, topic: str) -> int:
        """把 processing 里残留的消息搬回主列表（进程崩溃后的补偿）。返回条数。"""
        moved = 0
        while True:
            raw = await self._redis.rpoplpush(
                self._processing_key(topic), self._topic_key(topic)
            )
            if raw is None:
                break
            moved += 1
        if moved:
            log_event(task_log, logging.WARNING, "task inflight recovered", topic=topic, moved=moved)
        return moved

    async def recover(self, topics: Sequence[str] | None = None) -> int:
        total = 0
        for topic in topics or ():
            total += await self.recover_inflight(topic)
        return total

    async def replay_dead_letter(self, topic: str, *, limit: int = 10) -> int:
        """死信搬回主队列，`attempt` 重置为 1；返回条数。

        用 `RPOPLPUSH` 逐条搬（原子），再把搬过来的那条替换成 attempt=1 的副本：
        死信列表是 `LPUSH` 进的，尾部是最早的那条，先重放它符合"先进先出"。
        """
        if limit <= 0:
            return 0
        replayed = 0
        for _ in range(limit):
            raw = await self._redis.rpoplpush(self._dlq_key(topic), self._topic_key(topic))
            if raw is None:
                break
            await self._redis.lrem(self._topic_key(topic), 1, raw)
            try:
                message = TaskMessage.from_json(json.loads(raw))
            except (ValueError, KeyError, TypeError):
                # 坏到连结构都没有：留在死信里，别把主队列污染了
                await self._redis.lpush(self._dlq_key(topic), raw)
                continue
            retried = TaskMessage(
                id=message.id,
                topic=message.topic,
                key=message.key,
                payload=message.payload,
                attempt=1,
            )
            await self._redis.lpush(
                self._topic_key(topic), json.dumps(retried.to_json(), ensure_ascii=False)
            )
            replayed += 1
        if replayed:
            log_event(task_log, logging.WARNING, "task dead letter replayed",
                      topic=topic, replayed=replayed)
        return replayed

    async def sweep(self, topics: Sequence[str], *, older_than_s: float) -> int:
        """回收「取走太久还没 ack」的在途消息（进程被杀/卡死时的唯一出路）。

        判定依据是取用时刻（`{prefix}:{topic}:claimed` 的 score），不是消息创建时间——
        否则积压久的消息一被取走就会被误判成超时。
        搬回时 `attempt + 1`：真有消费者「一取就崩」时，最终会进死信而不是无限重投。
        """
        if older_than_s <= 0:
            return 0
        deadline = time.time() - older_than_s
        swept_total = 0
        for topic in topics:
            raw_items = await self._redis.zrangebyscore(self._claimed_key(topic), 0, deadline)
            swept = 0
            for raw in raw_items:
                # 先清登记：LREM 成功才说明它确实还卡在在途里
                removed = await self._redis.lrem(self._processing_key(topic), 1, raw)
                await self._redis.zrem(self._claimed_key(topic), raw)
                if not removed:
                    continue  # 已经被 ack/nack 掉了，只是登记没清干净
                try:
                    message = TaskMessage.from_json(json.loads(raw))
                except (ValueError, KeyError, TypeError):
                    await self._redis.lpush(self._dlq_key(topic), raw)
                    continue
                retried = TaskMessage(
                    id=message.id,
                    topic=message.topic,
                    key=message.key,
                    payload=message.payload,
                    attempt=min(message.attempt + 1, self._max_attempts),
                )
                await self._redis.lpush(
                    self._topic_key(topic), json.dumps(retried.to_json(), ensure_ascii=False)
                )
                swept += 1
            if swept:
                log_event(task_log, logging.WARNING, "task inflight swept",
                          topic=topic, swept=swept, timeout_s=older_than_s)
            swept_total += swept
        return swept_total

    async def aclose(self) -> None:
        closer: Awaitable[None] | None = getattr(self._redis, "aclose", None)
        if closer is not None:
            await closer()
