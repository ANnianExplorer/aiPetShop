"""工具网关：六道防线逐条钉死。任何一条被改松，这里立刻红。"""

from __future__ import annotations

from typing import Any

import pytest
from app.tools import (
    BackendClient,
    ToolAudit,
    ToolContext,
    ToolGateway,
    ToolPolicy,
    ToolRegistry,
    ToolSpec,
)
from pydantic import BaseModel, ConfigDict

from conftest import make_http

called: list[str] = []


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str = ""


async def echo(args: Args, ctx: ToolContext) -> dict[str, Any]:
    called.append("echo")
    return {"ok": True, "echo": args.q}


async def boom(args: Args, ctx: ToolContext) -> dict[str, Any]:
    raise RuntimeError("工具内部炸了")


async def write(args: Args, ctx: ToolContext) -> dict[str, Any]:
    called.append("write")
    return {"ok": True, "written": True}


def make_gateway(
    policy: ToolPolicy | None = None,
    *,
    max_calls: int = 3,
    auditor=None,
) -> ToolGateway:
    registry = ToolRegistry()
    registry.register(ToolSpec(name="echo", description="回显", args_model=Args, handler=echo))
    registry.register(ToolSpec(name="boom", description="总是失败", args_model=Args, handler=boom))
    registry.register(
        ToolSpec(
            name="write",
            description="写操作",
            args_model=Args,
            handler=write,
            side_effect=True,
        )
    )
    return ToolGateway(registry, policy, auditor=auditor, max_calls_per_run=max_calls)


def make_ctx(run_id: str = "r1", *, auto_commit: bool = False) -> ToolContext:
    return ToolContext(
        user_id="1001",
        token="token",
        run_id=run_id,
        backend=BackendClient("http://java/api/v1", "token", make_http()),
        pet_id=None,
        auto_commit=auto_commit,
    )


@pytest.fixture(autouse=True)
def _reset_called() -> None:
    called.clear()


async def test_unknown_tool() -> None:
    result = await make_gateway().invoke("nope", {}, make_ctx())
    assert (result.ok, result.code) == (False, "unknown_tool")


async def test_extra_field_is_rejected() -> None:
    # 模型伪造 user_id 越权：extra=forbid 直接拒
    result = await make_gateway().invoke("echo", {"q": "hi", "user_id": "9999"}, make_ctx())
    assert result.ok is False
    assert result.code == "invalid_arguments"
    assert "user_id" in (result.error or "")


async def test_schema_has_no_user_id() -> None:
    schemas = make_gateway(ToolPolicy(allow_side_effects=True)).schemas_for("app")
    props = {s["function"]["name"]: s["function"]["parameters"]["properties"] for s in schemas}
    assert all("user_id" not in p for p in props.values())
    assert set(props["write"]) == {"q"}


async def test_allowlist_blocks_unlisted_tool() -> None:
    gateway = make_gateway(ToolPolicy(allowed=frozenset({"echo"})))
    assert gateway.names_for("app") == ("echo",)
    result = await gateway.invoke("boom", {}, make_ctx())
    assert (result.ok, result.code) == (False, "tool_not_allowed")


async def test_channel_denied() -> None:
    gateway = make_gateway(ToolPolicy(channel_denied={"web": frozenset({"boom"})}))
    result = await gateway.invoke("boom", {}, make_ctx(), channel="web")
    assert result.code == "tool_not_allowed"
    assert "web" in (result.error or "")


async def test_side_effect_tool_only_proposes() -> None:
    gateway = make_gateway(ToolPolicy(allow_side_effects=True))
    result = await gateway.invoke("write", {"q": "x"}, make_ctx(auto_commit=False))
    assert result.ok is False
    assert result.code == "requires_confirmation"
    assert result.payload["status"] == "proposed"
    assert called == []  # 没有真的写


async def test_side_effect_runs_after_confirmation() -> None:
    gateway = make_gateway(ToolPolicy(allow_side_effects=True))
    result = await gateway.invoke("write", {"q": "x"}, make_ctx(auto_commit=True))
    assert result.ok is True
    assert called == ["write"]


async def test_side_effect_tool_hidden_by_default() -> None:
    # 部署默认策略：副作用工具不暴露给模型
    gateway = make_gateway()
    assert "write" not in gateway.names_for("app")
    result = await gateway.invoke("write", {"q": "x"}, make_ctx(auto_commit=True))
    assert (result.ok, result.code) == (False, "tool_not_allowed")


async def test_budget_per_run() -> None:
    gateway = make_gateway(max_calls=2)
    ctx = make_ctx()
    codes = [(await gateway.invoke("echo", {"q": "1"}, ctx)).code for _ in range(3)]
    assert codes == [None, None, "budget_exceeded"]
    assert gateway.calls_used("r1") == 2


async def test_error_is_contained() -> None:
    result = await make_gateway().invoke("boom", {}, make_ctx())
    assert (result.ok, result.code) == (False, "tool_failed")
    assert "RuntimeError" in (result.error or "")


async def test_audit_records_digest_not_raw() -> None:
    audits: list[ToolAudit] = []

    async def auditor(record: ToolAudit) -> None:
        audits.append(record)

    gateway = make_gateway(auditor=auditor)
    await gateway.invoke("echo", {"q": "敏感内容"}, make_ctx())
    assert len(audits) == 1
    assert len(audits[0].args_digest) == 16
    assert "敏感内容" not in audits[0].args_digest
