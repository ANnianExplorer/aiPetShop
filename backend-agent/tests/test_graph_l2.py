"""图：L1 直答不花 token，L2 走 ReAct 且 hop 上限生效。"""

from __future__ import annotations

from typing import Any

from conftest import make_http, make_settings

from app.domain.models import StepKind
from app.graph import build_graph
from app.llm import LLMReply, ScriptedModel, ToolCall
from app.tools import BackendClient, ToolGateway, ToolPolicy, build_registry


def make_graph(model: ScriptedModel, *, max_hops: int = 6) -> Any:
    settings = make_settings(max_tool_hops=max_hops)
    gateway = ToolGateway(build_registry(), ToolPolicy(), max_calls_per_run=4)

    def factory(token: str) -> BackendClient:
        return BackendClient("http://java/api/v1", token, make_http())

    return build_graph(model, gateway, settings, factory)


def state(question: str) -> dict[str, Any]:
    return {
        "question": question,
        "channel": "app",
        "user_id": "1001",
        "token": "token",
        "run_id": "run-test",
        "history": [],
        "citations": [],
        "hops": 0,
    }


async def test_l1_skips_model() -> None:
    model = ScriptedModel()
    result = await make_graph(model).ainvoke(state("你好"))

    assert model.calls == []
    assert [s.kind for s in result["steps"]] == [StepKind.ROUTE]
    assert result["answer_messages"][-1] == {"role": "user", "content": "你好"}


async def test_l2_runs_tool_then_answers() -> None:
    model = ScriptedModel(
        replies=[
            LLMReply(
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="search_logs",
                        arguments={"keyword": "疫苗"},
                        raw_arguments='{"keyword": "疫苗"}',
                    )
                ]
            ),
            LLMReply(text="9 月 1 日打过加强针。"),
        ]
    )
    result = await make_graph(model).ainvoke(state("上次疫苗是什么时候"))

    assert [s.kind for s in result["steps"]] == [
        StepKind.ROUTE,
        StepKind.LLM,
        StepKind.TOOL,
        StepKind.LLM,
    ]
    tool_step = result["steps"][2]
    assert (tool_step.name, tool_step.status.value) == ("search_logs", "ok")

    tool_messages = [m for m in result["messages"] if m["role"] == "tool"]
    assert "7001" in tool_messages[0]["content"]

    assert result["citations"][0].kind == "log"
    assert result["answer_messages"][-1]["content"] == "9 月 1 日打过加强针。"
    assert set(model.tool_names) == {
        "get_pet_profile",
        "get_health_summary",
        "search_logs",
        "search_posts",
    }
    # 回归：L2 第一次调用模型时必须已经带上 system + 用户问题，
    # 否则模型在"空对话"里出牌（曾因 route→agent 跳过 prepare 而踩过）。
    first_call = model.calls[0]
    assert first_call[0]["role"] == "system"
    assert first_call[-1] == {"role": "user", "content": "上次疫苗是什么时候"}


async def test_hop_limit_stops_loop() -> None:
    model = ScriptedModel(
        replies=[
            LLMReply(tool_calls=[ToolCall(id="c1", name="get_pet_profile", arguments={})]),
            LLMReply(tool_calls=[ToolCall(id="c2", name="get_pet_profile", arguments={})]),
        ]
    )
    result = await make_graph(model, max_hops=1).ainvoke(state("看看它的档案"))

    assert len(model.calls) == 2  # 第二轮不再执行工具
    assert [s.kind for s in result["steps"]].count(StepKind.TOOL) == 1
    assert "answer_messages" not in result  # 交给 runner 兜底文案


async def test_invalid_tool_arguments_do_not_crash() -> None:
    model = ScriptedModel(
        replies=[
            LLMReply(
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="search_logs",
                        arguments={"keyword": "疫苗"},
                        raw_arguments='{"keyword": "疫苗", "limit": 999}',
                    )
                ]
            ),
            LLMReply(text="参数不合法。"),
        ]
    )
    result = await make_graph(model).ainvoke(state("搜索疫苗记录"))
    tool_step = result["steps"][2]
    assert tool_step.status.value == "error"
    assert tool_step.error and "limit" in tool_step.error
