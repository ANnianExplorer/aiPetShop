"""图装配：边和条件边集中在这里，节点实现见 `nodes.py`。"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from ..config import Settings
from ..llm.base import ChatModel
from ..tools import ToolGateway
from .nodes import BackendFactory, make_nodes
from .state import AgentState


def build_graph(
    model: ChatModel,
    gateway: ToolGateway,
    settings: Settings,
    backend_factory: BackendFactory,
    checkpointer: Any = None,
    docs: Any = None,
) -> Any:
    nodes = make_nodes(
        model,
        gateway,
        backend_factory,
        max_hops=settings.max_tool_hops,
        max_tokens=settings.run_token_budget,
        docs=docs,
    )

    graph = StateGraph(AgentState)
    graph.add_node("route", nodes["route"])
    graph.add_node("prepare", nodes["prepare"])
    graph.add_node("agent", nodes["agent"])
    graph.add_node("tools", nodes["tools"])

    graph.add_edge(START, "route")
    # 先拼上下文，再决定走不走工具循环：
    # L1 只拼上下文就结束（首 token 不等工具），L2 从 agent 开始决策。
    graph.add_edge("route", "prepare")
    graph.add_conditional_edges("prepare", nodes["_after_route"], {"direct": END, "react": "agent"})
    graph.add_conditional_edges("agent", nodes["_after_agent"], {"tools": "tools", "done": END})
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
