"""记忆层：抽取（extract）→ 决策（ops）→ 服务（service）。

目录边界与存储层一致：这里不 import 存储实现，只依赖 `AgentRepository` 协议。
"""

from .extract import FACT_LABELS, MemoryCandidate, extract, label_of
from .ops import Decision, MemoryOp, decide, normalize
from .service import MemoryService

__all__ = [
    "FACT_LABELS",
    "Decision",
    "MemoryCandidate",
    "MemoryOp",
    "MemoryService",
    "decide",
    "extract",
    "label_of",
    "normalize",
]
