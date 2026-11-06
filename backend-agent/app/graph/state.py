"""图状态：节点之间唯一的通信载体。

`messages` 与 `steps` 是累加语义（`operator.add`）——节点只返回自己新增的那部分，
召回式的「读-改-写」会在并发分支下丢数据，这是 LangGraph 里最常见的坑之一。
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from ..domain.models import Citation, Intent, Route, Step


class AgentState(TypedDict, total=False):
    # 输入（由 runtime 注入）
    question: str
    channel: str
    user_id: str
    token: str
    pet_id: str | None
    run_id: str
    history: list[dict[str, Any]]

    # 过程
    route: Route
    intent: Intent
    messages: Annotated[list[dict[str, Any]], operator.add]
    steps: Annotated[list[Step], operator.add]
    citations: list[Citation]
    hops: int
    # 用量按累加：一次 run 可能有多轮 LLM 调用，覆盖式写入会少算
    prompt_tokens: Annotated[int, operator.add]
    completion_tokens: Annotated[int, operator.add]

    # 输出
    answer_messages: list[dict[str, Any]]
