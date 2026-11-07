"""Redis 客户端工厂：统一 RESP2。

为什么钉死 RESP2：`redis-py` 8.x 默认用 RESP3 握手（`HELLO 3`），而本机 Redis 5.0.14
不实现 `HELLO`，连接会直接抛 `ResponseError: unknown command 'HELLO'`——一个只在真机
才暴露、测试替身永远发现不了的故障（见 reports/2026-11-08-s1.8-p2.md 的 D1）。

我们只用 `INCR/EXPIRE/XADD/XRANGE`，这些命令在 RESP2 下语义完全一致，所以统一降级
换成 RESP2，而不是写「先试 3 再回退 2」的两段式握手（少一次往返、少一条分支）。
"""

from __future__ import annotations

from typing import Any


def create_redis(url: str) -> Any:
    """按 RESP2 建客户端；调用方负责 `aclose()`。"""
    from redis.asyncio import from_url

    return from_url(
        url,
        encoding="utf-8",
        decode_responses=True,
        protocol=2,
        socket_connect_timeout=5.0,
        socket_timeout=5.0,
        health_check_interval=30,
    )
