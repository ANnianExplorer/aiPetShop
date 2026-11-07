"""记忆算子：决定一条新事实对已有记忆是「新增 / 更新 / 无事发生」。

mem0 把记忆当算子而不是"存一段文本"，这里落的是最小可验证版本：
- 归一化后相同 → NOOP（防止同一句话反复说把表撑爆）；
- key 相同但值不同 → UPDATE（宠物改名、体重变化都属于同一事实的演化）；
- 没有记录 → ADD。
删除不从对话里推导（用户说"它不再过敏了"这种否定句太容易误判），走管理端显式操作。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MemoryOp(str, Enum):
    ADD = "add"
    UPDATE = "update"
    NOOP = "noop"


@dataclass(frozen=True)
class Decision:
    op: MemoryOp
    reason: str


def normalize(value: str) -> str:
    return "".join(value.split()).lower()


def decide(existing_value: str | None, new_value: str) -> Decision:
    if existing_value is None:
        return Decision(MemoryOp.ADD, "new_fact")
    if normalize(existing_value) == normalize(new_value):
        return Decision(MemoryOp.NOOP, "same_value")
    return Decision(MemoryOp.UPDATE, "value_changed")
