"""图节点：每个节点只做一件事，全部依赖注入，测试里可以直接换掉。

- route：确定性意图分类（不花 token）；
- prepare：拼最终回答的上下文（system + 历史 + 当前问题）；
- agent：一次模型决策，可能带 tool_calls；
- react_tools：批量执行工具，结果按 `role=tool` 回灌。
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from ..core.errors import BudgetExceeded
from ..domain.models import Citation, Route, Step, StepKind, StepStatus, ToolResult
from ..domain.router import classify
from ..llm.base import ChatModel
from ..tools import BackendClient, ToolContext, ToolGateway

# 提示词正文搬到了 `prompts.py`（版本登记表 + 冻结哈希）：这里只负责引用，
# 改正文请按那份文件顶部的约定登记新版本，不要原地改。
from .prompts import SYSTEM_PROMPT
from .state import AgentState

BackendFactory = Callable[[str], BackendClient]


def make_nodes(
    model: ChatModel,
    gateway: ToolGateway,
    backend_factory: BackendFactory,
    *,
    max_hops: int,
    max_tokens: int = 0,
    docs: Any = None,
) -> dict[str, Callable[[AgentState], Any]]:
    async def route_node(state: AgentState) -> dict[str, Any]:
        decision = classify(state["question"])
        return {
            "intent": decision.intent,
            "route": decision.route,
            "hops": 0,
            "steps": [
                Step(
                    seq=0,
                    kind=StepKind.ROUTE,
                    name="classify",
                    input={"intent": decision.intent.value, "reason": decision.reason},
                )
            ],
        }

    async def prepare_node(state: AgentState) -> dict[str, Any]:
        system = SYSTEM_PROMPT
        memory_lines = list(state.get("memory_lines") or [])
        if memory_lines:
            # 记忆拼在 system 里而不是伪造一轮 user 消息：模型不会把它当成"用户刚说的"
            system += "\n\n已知的这只宠物的事实（来自你之前的对话，可直接使用）：\n" + "\n".join(
                f"- {line}" for line in memory_lines
            )
        profile_lines = list(state.get("profile_lines") or [])
        if profile_lines:
            # 画像只放「风险 / 待办」：事实明细已经在上面，重复注入只会浪费 token
            system += "\n\n这只宠物的画像摘要（长期风险与待办，回答相关问题时优先考虑）：\n" + "\n".join(
                f"- {line}" for line in profile_lines
            )
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        messages.extend(state.get("history") or [])
        messages.append({"role": "user", "content": state["question"]})
        update: dict[str, Any] = {"messages": messages}
        if state.get("route") == Route.L1:
            # L1 没有工具循环：上下文拼好就能直接生成，省一次模型往返。
            update["answer_messages"] = messages
        return update

    async def agent_node(state: AgentState) -> dict[str, Any]:
        started = time.perf_counter()
        messages = list(state["messages"])
        reply = await model.complete(messages, gateway.schemas_for(state["channel"]))

        spent = (
            int(state.get("prompt_tokens") or 0)
            + int(state.get("completion_tokens") or 0)
            + reply.usage.total
        )
        if max_tokens and spent > max_tokens:
            # 在下一轮工具/生成之前叫停：已经烧掉的算沉没成本，不能再滚
            raise BudgetExceeded(f"本次对话已超过 {max_tokens} token 预算")

        assistant: dict[str, Any] = {"role": "assistant", "content": reply.text}
        if reply.tool_calls:
            assistant["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": call.raw_arguments
                        or json.dumps(call.arguments, ensure_ascii=False),
                    },
                }
                for call in reply.tool_calls
            ]

        update: dict[str, Any] = {
            "messages": [assistant],
            "steps": [
                Step(
                    seq=0,
                    kind=StepKind.LLM,
                    name="agent",
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    input={"tool_count": len(reply.tool_calls)},
                )
            ],
            "prompt_tokens": reply.usage.prompt_tokens,
            "completion_tokens": reply.usage.completion_tokens,
        }
        if not reply.tool_calls:
            update["answer_messages"] = [*messages, assistant]
        return update

    async def tools_node(state: AgentState) -> dict[str, Any]:
        last = state["messages"][-1]
        ctx = ToolContext(
            user_id=state["user_id"],
            token=state["token"],
            run_id=state["run_id"],
            backend=backend_factory(state["token"]),
            pet_id=state.get("pet_id"),
            docs=docs,
        )
        tool_messages: list[dict[str, Any]] = []
        steps: list[Step] = []
        citations: list[Citation] = list(state.get("citations") or [])

        for call in last.get("tool_calls") or []:
            fn = call.get("function") or {}
            name = str(fn.get("name") or "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
                if not isinstance(args, dict):
                    raise ValueError("参数必须是 JSON 对象")
            except (json.JSONDecodeError, ValueError) as exc:
                result = ToolResult(ok=False, code="invalid_arguments", error=f"参数不是合法 JSON：{exc}")
                args = {}
            else:
                result = await gateway.invoke(name, args, ctx, state["channel"])

            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "content": result.to_model_content(),
                }
            )
            status = StepStatus.OK if result.ok else StepStatus.ERROR
            if result.code == "requires_confirmation":
                status = StepStatus.PROPOSED
            elif result.code == "tool_not_allowed":
                status = StepStatus.DENIED
            steps.append(
                Step(
                    seq=0,
                    kind=StepKind.TOOL,
                    name=name,
                    status=status,
                    latency_ms=result.latency_ms,
                    input=args,
                    output_digest=json.dumps(result.payload, ensure_ascii=False, default=str)[:500],
                    error=result.error,
                )
            )
            for raw in result.payload.get("citations") or []:
                if isinstance(raw, dict):
                    citations.append(Citation.from_dict(raw))

        return {
            "messages": tool_messages,
            "steps": steps,
            "hops": int(state.get("hops") or 0) + 1,
            "citations": citations,
        }

    def after_route(state: AgentState) -> str:
        return "react" if state.get("route") and state["route"].value == "L2" else "direct"

    def after_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        wants_tools = bool(last.get("tool_calls"))
        hops = int(state.get("hops") or 0)
        return "tools" if wants_tools and hops < max_hops else "done"

    return {
        "route": route_node,
        "prepare": prepare_node,
        "agent": agent_node,
        "tools": tools_node,
        "_after_route": after_route,
        "_after_agent": after_agent,
    }
