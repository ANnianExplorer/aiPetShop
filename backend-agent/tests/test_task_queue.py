"""任务队列契约测试（at-least-once / 重试 / 死信 / 幂等）。

两个实现跑同一套语义断言：进程内与 Redis 列表必须表现一致，
否则「本地好了线上不一样」又会重演。
"""

from __future__ import annotations

import asyncio
import json
import time

import pytest

from app.memory import MemoryService
from app.storage.memory import InMemoryRepository
from app.tasks import (
    TOPIC_AUDIT_TOOL,
    TOPIC_MEMORY_OBSERVE,
    InProcessTaskQueue,
    RedisTaskQueue,
    TaskWorker,
)
from app.tasks.base import TaskMessage, backoff_seconds
from app.tasks.consumers import build_handlers


class FakeRedis:
    """只实现队列用到的命令：LPUSH / RPOPLPUSH / LREM / LLEN / LRANGE + ZSET 三件套。"""

    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.zsets: dict[str, dict[str, float]] = {}
        self.closed = False

    async def lpush(self, key: str, *values: str) -> int:
        bucket = self.lists.setdefault(key, [])
        for value in values:
            bucket.insert(0, value)
        return len(bucket)

    async def rpoplpush(self, src: str, dst: str) -> str | None:
        source = self.lists.get(src) or []
        if not source:
            return None
        value = source.pop()
        self.lists.setdefault(dst, []).insert(0, value)
        return value

    async def brpoplpush(self, src: str, dst: str, timeout: int) -> str | None:
        return await self.rpoplpush(src, dst)

    async def lrem(self, key: str, count: int, value: str) -> int:
        bucket = self.lists.get(key) or []
        removed = 0
        while value in bucket:
            bucket.remove(value)
            removed += 1
            if count and removed >= count:
                break
        return removed

    async def llen(self, key: str) -> int:
        return len(self.lists.get(key) or [])

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        bucket = self.lists.get(key) or []
        return bucket[start:] if end == -1 else bucket[start : end + 1]

    # ---- ZSET（在途登记）----
    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        bucket = self.zsets.setdefault(key, {})
        added = 0
        for member, score in mapping.items():
            if member not in bucket:
                added += 1
            bucket[member] = float(score)
        return added

    async def zrem(self, key: str, *values: str) -> int:
        bucket = self.zsets.get(key) or {}
        removed = 0
        for value in values:
            if bucket.pop(value, None) is not None:
                removed += 1
        return removed

    async def zrangebyscore(self, key: str, minimum: float, maximum: float) -> list[str]:
        bucket = self.zsets.get(key) or {}
        picked = [(score, member) for member, score in bucket.items() if minimum <= score <= maximum]
        return [member for _score, member in sorted(picked)]

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture(params=["inprocess", "redis"])
def queue(request: pytest.FixtureRequest):
    if request.param == "inprocess":
        return InProcessTaskQueue(topic="t", max_attempts=2)
    return RedisTaskQueue(FakeRedis(), max_attempts=2)


async def test_publish_receive_ack(queue) -> None:
    message_id = await queue.publish("t", key="u1:r1", payload={"text": "hi"})
    assert len(message_id) == 19

    message = await queue.receive("t", timeout_s=0.05)
    assert message is not None
    assert message.key == "u1:r1"
    assert message.payload["text"] == "hi"
    assert message.attempt == 1

    await queue.ack(message)
    assert await queue.depth("t") == 0
    assert await queue.receive("t", timeout_s=0.05) is None


async def test_nack_retries_then_dead_letters(queue) -> None:
    await queue.publish("t", key="k", payload={"n": 1})
    first = await queue.receive("t", timeout_s=0.05)
    assert first is not None
    await queue.nack(first, error="boom")

    # B4：失败不立刻回主队列，先进退避队列（否则下游抖动会变成热循环）
    assert await queue.depth("t") == 0
    assert await queue.receive("t", timeout_s=0.05) is None
    promoted = await queue.retry_due(["t"], now=time.time() + 3600)
    assert promoted == 1

    second = await queue.receive("t", timeout_s=0.05)
    assert second is not None
    assert second.attempt == 2
    assert second.id == first.id  # 同一条消息，只加尝试次数

    await queue.nack(second, error="boom again")
    assert await queue.depth("t") == 0
    assert await queue.receive("t", timeout_s=0.05) is None
    dead = await queue.dead_letters("t")
    assert len(dead) == 1
    assert dead[0].key == "k"


async def test_receive_does_not_lose_message_on_ack_miss(queue) -> None:
    """没 ack 就断了：Redis 实现能 recover，进程内实现不承诺（文档里写明）。"""
    await queue.publish("t", key="k", payload={})
    message = await queue.receive("t", timeout_s=0.05)
    assert message is not None
    if isinstance(queue, RedisTaskQueue):
        assert await queue.recover_inflight("t") == 1
        again = await queue.receive("t", timeout_s=0.05)
        assert again is not None
        assert again.id == message.id


async def test_inprocess_queue_full_raises() -> None:
    queue = InProcessTaskQueue(topic="t", max_size=1)
    await queue.publish("t", key="k1", payload={})
    with pytest.raises(Exception) as exc:
        await queue.publish("t", key="k2", payload={})
    assert "已满" in str(exc.value)


async def test_worker_dispatches_and_retries() -> None:
    # B4：重试先退避，worker 的巡检负责到期搬回；这里把退避压到 0 让用例可确定
    queue = InProcessTaskQueue(topic=TOPIC_MEMORY_OBSERVE, max_attempts=2, retry_base_s=0.0, retry_cap_s=0.0)
    seen: list[TaskMessage] = []
    attempts = {"n": 0}

    async def flaky(message: TaskMessage) -> None:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("第一次失败")
        seen.append(message)

    worker = TaskWorker(queue, {TOPIC_MEMORY_OBSERVE: flaky}, sweep_interval_s=0.01)
    await worker.start()
    try:
        await queue.publish(TOPIC_MEMORY_OBSERVE, key="k", payload={})
        await _wait_until(lambda: len(seen) == 1)
    finally:
        await worker.stop()

    assert seen[0].attempt == 2
    assert worker.processed == 1
    assert worker.failed == 1


async def test_worker_dead_letters_after_max_attempts() -> None:
    queue = InProcessTaskQueue(
        topic=TOPIC_AUDIT_TOOL, max_attempts=2, retry_base_s=0.0, retry_cap_s=0.0
    )

    async def always_fail(_: TaskMessage) -> None:
        raise RuntimeError("永久失败")

    worker = TaskWorker(queue, {TOPIC_AUDIT_TOOL: always_fail}, sweep_interval_s=0.01)
    await worker.start()
    try:
        await queue.publish(TOPIC_AUDIT_TOOL, key="k", payload={})
        await _wait_until_async(lambda: _has_dead(queue))
    finally:
        await worker.stop()

    assert worker.failed == 2
    assert worker.processed == 0
    assert worker.promoted >= 1  # 至少一次「退避到期搬回」


async def _has_dead(queue) -> bool:
    return len(await queue.dead_letters(TOPIC_AUDIT_TOOL)) == 1


async def test_memory_consumer_writes_fact() -> None:
    repo = InMemoryRepository()
    memory = MemoryService(repo)
    queue = InProcessTaskQueue(topic=TOPIC_MEMORY_OBSERVE, max_attempts=2)
    worker = TaskWorker(queue, build_handlers(memory, repo))
    await worker.start()
    try:
        await queue.publish(
            TOPIC_MEMORY_OBSERVE,
            key="1001:r1",
            payload={"user_id": "1001", "pet_id": None, "text": "我家猫叫Lumina，对牛奶过敏"},
        )
        await _wait_until(lambda: len(repo._facts) == 2)
    finally:
        await worker.stop()

    facts = await repo.list_memory_facts("1001", None)
    assert {fact.key for fact in facts} == {"pet_name", "allergy"}


async def test_memory_consumer_writes_episode_with_source_message() -> None:
    repo = InMemoryRepository()
    memory = MemoryService(repo)
    handlers = build_handlers(memory, repo)
    message = TaskMessage(
        id="1794027476119000002",
        topic=TOPIC_MEMORY_OBSERVE,
        key="1001:r2",
        payload={
            "user_id": "1001",
            "pet_id": None,
            "text": "上周给豆豆洗澡了",
            "session_id": "77",
            "message_id": "9001",
            "run_id": "r2",
        },
    )

    await handlers[TOPIC_MEMORY_OBSERVE](message)
    await handlers[TOPIC_MEMORY_OBSERVE](message)  # 队列重复投递

    episodes = await repo.list_memory_episodes("1001", None)
    assert len(episodes) == 1
    assert episodes[0].kind == "bath"
    assert episodes[0].session_id == "77"
    assert episodes[0].source_message_id == "9001"


async def test_audit_consumer_is_idempotent_on_duplicate_delivery() -> None:
    repo = InMemoryRepository()
    memory = MemoryService(repo)
    handlers = build_handlers(memory, repo)
    payload = {
        "run_id": "1794027476119000000",
        "name": "get_pet_profile",
        "ok": True,
        "code": None,
        "latency_ms": 12,
        "args_digest": "abcdef0123456789",
    }
    message = TaskMessage(id="1794027476119000001", topic=TOPIC_AUDIT_TOOL, key="k", payload=payload)

    await handlers[TOPIC_AUDIT_TOOL](message)
    await handlers[TOPIC_AUDIT_TOOL](message)  # 队列重复投递

    assert len(repo.tool_calls()) == 1


async def _wait_until(predicate, timeout_s: float = 2.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while loop.time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("等待条件超时")


async def _wait_until_async(predicate, timeout_s: float = 2.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while loop.time() < deadline:
        if await predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("等待条件超时")


def test_redis_payload_is_json_roundtrip() -> None:
    raw = json.dumps(
        TaskMessage(id="1", topic="t", key="k", payload={"a": [1, 2]}).to_json(), ensure_ascii=False
    )
    parsed = TaskMessage.from_json(json.loads(raw))
    assert parsed.payload == {"a": [1, 2]}


async def test_recover_returns_inflight_messages(queue) -> None:
    """启动补偿：进程崩溃时卡在「在途」的消息必须能回到待消费队列。"""
    await queue.publish("t", key="k", payload={})
    message = await queue.receive("t", timeout_s=0.05)
    assert message is not None

    recovered = await queue.recover(["t"])
    if isinstance(queue, RedisTaskQueue):
        assert recovered == 1
        again = await queue.receive("t", timeout_s=0.05)
        assert again is not None and again.id == message.id
    else:
        # 内存实现没有在途态：消息被取走就是被取走，不做假承诺
        assert recovered == 0


async def test_replay_dead_letter_resets_attempt(queue) -> None:
    await queue.publish("t", key="k", payload={"n": 1})
    for _ in range(2):  # max_attempts=2：第 2 次 nack 进死信
        message = await queue.receive("t", timeout_s=0.05)
        assert message is not None
        await queue.nack(message, error="boom")
        await queue.retry_due(["t"], now=time.time() + 3600)

    dead = await queue.dead_letters("t")
    assert len(dead) == 1
    assert dead[0].attempt == 2

    assert await queue.replay_dead_letter("t", limit=10) == 1
    assert await queue.dead_letters("t") == []
    assert await queue.depth("t") == 1

    replayed = await queue.receive("t", timeout_s=0.05)
    assert replayed is not None
    assert replayed.id == dead[0].id
    assert replayed.attempt == 1  # 重新开始计数，否则一失败就又进死信


async def test_replay_dead_letter_respects_limit(queue) -> None:
    for index in range(3):
        await queue.publish("t", key=f"k{index}", payload={})
        message = await queue.receive("t", timeout_s=0.05)
        assert message is not None
        await queue.nack(message, error="boom")
        await queue.retry_due(["t"], now=time.time() + 3600)
        message = await queue.receive("t", timeout_s=0.05)
        assert message is not None
        await queue.nack(message, error="boom")
    assert len(await queue.dead_letters("t")) == 3

    assert await queue.replay_dead_letter("t", limit=2) == 2
    assert len(await queue.dead_letters("t")) == 1
    assert await queue.depth("t") == 2


async def test_sweep_reclaims_stale_inflight(queue) -> None:
    """B3：取走后卡死没 ack 的消息，必须能被巡检搬回（attempt+1）。"""
    await queue.publish("t", key="k1", payload={"n": 1})
    message = await queue.receive("t", timeout_s=0.05)
    assert message is not None

    if not isinstance(queue, RedisTaskQueue):
        # 内存实现不假装能扫跨进程在途
        assert await queue.sweep(["t"], older_than_s=0.01) == 0
        return

    # 把取用时刻改到 100s 之前，模拟消费者卡死
    raw = json.dumps(message.to_json(), ensure_ascii=False)
    queue._redis.zsets["pet:task:t:claimed"][raw] = time.time() - 100

    assert await queue.sweep(["t"], older_than_s=1) == 1
    assert await queue.depth("t") == 1
    assert queue._redis.zsets["pet:task:t:claimed"] == {}

    again = await queue.receive("t", timeout_s=0.05)
    assert again is not None and again.id == message.id and again.attempt == 2
    await queue.ack(again)
    assert await queue.sweep(["t"], older_than_s=1) == 0


async def test_sweep_ignores_acked_messages(queue) -> None:
    """已 ack 的消息不能被巡检误搬回队列（登记残留要能自愈）。"""
    await queue.publish("t", key="k2", payload={})
    message = await queue.receive("t", timeout_s=0.05)
    assert message is not None
    await queue.ack(message)

    if isinstance(queue, RedisTaskQueue):
        # 人为留一条过期登记，验证 sweep 不会把不存在的在途搬回去
        raw = json.dumps(message.to_json(), ensure_ascii=False)
        queue._redis.zsets.setdefault("pet:task:t:claimed", {})[raw] = time.time() - 100

    assert await queue.sweep(["t"], older_than_s=1) == 0
    assert await queue.depth("t") == 0

# --- B4 退避与有界重投 -------------------------------------------------------


def test_backoff_grows_and_caps() -> None:
    assert backoff_seconds(1) == 5.0
    assert backoff_seconds(2) == 10.0
    assert backoff_seconds(5) == 80.0
    assert backoff_seconds(100) == 600.0  # 封顶，不能指数爆炸
    assert backoff_seconds(1, base=0.0) == 0.0
    assert backoff_seconds(-3) == 5.0  # 非法次数按首次算


async def test_retry_not_promoted_before_due(queue) -> None:
    await queue.publish("t", key="k", payload={})
    message = await queue.receive("t", timeout_s=0.05)
    assert message is not None
    await queue.nack(message, error="boom")

    # 还没到期：不能提前搬回，否则退避等于没做
    assert await queue.retry_due(["t"], now=time.time()) == 0
    assert await queue.depth("t") == 0
    assert await queue.retry_due(["t"], now=time.time() + 3600) == 1
    assert await queue.depth("t") == 1


async def test_redrive_dead_letters_respects_max_redrives(queue) -> None:
    await queue.publish("t", key="k", payload={})
    for _ in range(2):
        message = await queue.receive("t", timeout_s=0.05)
        assert message is not None
        await queue.nack(message, error="boom")
        await queue.retry_due(["t"], now=time.time() + 3600)
    assert len(await queue.dead_letters("t")) == 1

    # 上限 0：一条都不许自动放回（默认关闭的语义）
    assert await queue.redrive_dead_letters(["t"], limit_per_topic=5, max_redrives=0) == 0
    assert len(await queue.dead_letters("t")) == 1

    # 上限 1：放回一次并记 redrives=1
    assert await queue.redrive_dead_letters(["t"], limit_per_topic=5, max_redrives=1) == 1
    replayed = await queue.receive("t", timeout_s=0.05)
    assert replayed is not None
    assert replayed.attempt == 1 and replayed.redrives == 1

    # 再失败两次回到死信；此时 redrives 已达上限，不许再放回
    for _ in range(2):
        await queue.nack(replayed, error="boom")
        await queue.retry_due(["t"], now=time.time() + 3600)
        nxt = await queue.receive("t", timeout_s=0.05)
        if nxt is not None:
            replayed = nxt
    assert len(await queue.dead_letters("t")) == 1
    assert await queue.redrive_dead_letters(["t"], limit_per_topic=5, max_redrives=1) == 0