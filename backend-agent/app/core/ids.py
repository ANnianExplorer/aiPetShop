"""单调递增的 19 位 ID（对齐 MySQL BIGINT 与 Java `Long → String`）。

结构：13 位毫秒时间戳 + 2 位节点号 + 4 位毫秒内序号 = 19 位十进制。
约束：时间戳首位为 1（当前年代），整体 < 9.22e18，能塞进 signed BIGINT；
      单节点单毫秒最多 9999 个 ID，超了自旋到下一毫秒。
时钟回拨：沿用上一次时间戳并递增序号，宁可重复 ID 也绝不产生倒退。
"""

from __future__ import annotations

import threading
import time

_MAX_SEQ = 9999


class IdGenerator:
    def __init__(self, node_id: int = 0) -> None:
        if not 0 <= node_id <= 99:
            raise ValueError("node_id 必须在 0..99 之间，否则会撑破 19 位 BIGINT")
        self._node = node_id
        self._lock = threading.Lock()
        self._last_ts = 0
        self._seq = 0

    def next(self) -> str:
        with self._lock:
            ts = int(time.time() * 1000)
            if ts > self._last_ts:
                self._last_ts, self._seq = ts, 0
            else:
                # 同一毫秒或时钟回拨：沿用 last_ts，序号自增
                ts = self._last_ts
                self._seq += 1
                if self._seq > _MAX_SEQ:
                    while ts <= self._last_ts:
                        time.sleep(0.0005)
                        ts = int(time.time() * 1000)
                    self._last_ts, self._seq = ts, 0
            return f"{ts:013d}{self._node:02d}{self._seq:04d}"


_DEFAULT = IdGenerator()


def new_id() -> str:
    return _DEFAULT.next()
