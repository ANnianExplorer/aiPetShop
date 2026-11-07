"""配额限流：窗口语义、失败开放、两套实现行为一致。"""

from __future__ import annotations

import pytest

from app.core.ratelimit import InMemoryRateLimiter, RedisRateLimiter


class FakeClock:
    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class FakeRedis:
    """只实现限流用到的最小命令集；pipeline 串行执行，语义与 redis-py 一致。"""

    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expires: dict[str, int] = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    def incr(self, key: str) -> int:
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    def expire(self, key: str, ttl: int) -> bool:
        self.expires[key] = int(ttl)
        return True


class FakePipeline:
    def __init__(self, client: FakeRedis) -> None:
        self._client = client
        self._ops: list[tuple[str, tuple]] = []

    def incr(self, key: str) -> FakePipeline:
        self._ops.append(("incr", (key,)))
        return self

    def expire(self, key: str, ttl: int) -> FakePipeline:
        self._ops.append(("expire", (key, ttl)))
        return self

    async def execute(self) -> list:
        return [getattr(self._client, name)(*args) for name, args in self._ops]


@pytest.mark.asyncio
async def test_minute_window_blocks_after_limit() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(3, 100, clock=clock)

    decisions = [await limiter.hit("u1") for _ in range(3)]
    assert all(d.allowed for d in decisions)
    assert decisions[-1].remaining == 0
    assert [d.remaining for d in decisions] == [2, 1, 0]

    blocked = await limiter.hit("u1")
    assert blocked.allowed is False
    assert blocked.limit == 3
    assert 1 <= blocked.retry_after_s <= 61


@pytest.mark.asyncio
async def test_minute_window_recovers_after_60s() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(2, 100, clock=clock)
    await limiter.hit("u1")
    await limiter.hit("u1")
    assert (await limiter.hit("u1")).allowed is False

    clock.now += 61
    assert (await limiter.hit("u1")).allowed is True


@pytest.mark.asyncio
async def test_day_limit_is_independent_of_minute() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(1, 2, clock=clock)
    assert (await limiter.hit("u1")).allowed is True
    clock.now += 61
    assert (await limiter.hit("u1")).allowed is True
    clock.now += 61
    blocked = await limiter.hit("u1")
    assert blocked.allowed is False
    assert blocked.limit == 2


@pytest.mark.asyncio
async def test_users_are_isolated() -> None:
    limiter = InMemoryRateLimiter(1, 10)
    assert (await limiter.hit("u1")).allowed is True
    assert (await limiter.hit("u2")).allowed is True
    assert (await limiter.hit("u1")).allowed is False


@pytest.mark.asyncio
async def test_scopes_are_isolated() -> None:
    limiter = InMemoryRateLimiter(1, 10)
    assert (await limiter.hit("u1", "chat")).allowed is True
    assert (await limiter.hit("u1", "upload")).allowed is True


@pytest.mark.asyncio
async def test_redis_limiter_counts_and_blocks() -> None:
    client = FakeRedis()
    limiter = RedisRateLimiter(client, 2, 10)
    first = await limiter.hit("u1")
    second = await limiter.hit("u1")
    third = await limiter.hit("u1")
    assert (first.allowed, second.allowed, third.allowed) == (True, True, False)
    assert third.retry_after_s >= 1
    # 键带窗口后缀，并设置了过期，不会无限增长
    assert all(ttl > 0 for ttl in client.expires.values())


@pytest.mark.asyncio
async def test_redis_limiter_fails_open_when_backend_down() -> None:
    class Broken:
        def pipeline(self):
            raise RuntimeError("redis down")

    limiter = RedisRateLimiter(Broken(), 1, 1)
    decision = await limiter.hit("u1")
    assert decision.allowed is True, "配额设施故障不能变成全站不可用"
