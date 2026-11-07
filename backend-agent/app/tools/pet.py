"""宠物只读工具：全部走 Java 业务后端取数，单一真源，不直连业务表。

端点（已与 controller 核对）：
    GET  /pet/list                     -> List<PetVO>
    GET  /pet/get/vo?id=               -> PetVO
    GET  /health/dashboard?petId=      -> HealthDashboardVO
    GET  /health/record/weekly?petId=  -> List<HealthRecordVO>
    POST /log/list/page/vo             -> IPage<LogEntryVO>  body: {petId, searchText, current, pageSize}
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .registry import ToolRegistry
from .spec import ToolContext, ToolSpec


class PetScopedArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pet_id: str | None = Field(
        default=None,
        pattern=r"^\d{1,19}$",
        description="宠物 ID（纯数字，最多 19 位）；省略时使用当前会话绑定的宠物",
    )


class SearchLogsArgs(PetScopedArgs):
    keyword: str | None = Field(default=None, max_length=64, description="检索关键词，如 疫苗 / 呕吐 / 洗澡")
    limit: int = Field(default=5, ge=1, le=20, description="返回条数，1~20，默认 5")


def _pet_id(args: PetScopedArgs, ctx: ToolContext) -> str | None:
    return args.pet_id or ctx.pet_id or None


async def get_pet_profile(args: PetScopedArgs, ctx: ToolContext) -> dict[str, Any]:
    pet_id = _pet_id(args, ctx)
    if pet_id:
        data = await ctx.backend.get("/pet/get/vo", {"id": pet_id})
        pets = [data] if data else []
    else:
        pets = await ctx.backend.get("/pet/list") or []
    return {
        "ok": True,
        "pets": pets,
        "citations": [
            {
                "kind": "pet",
                "id": str(p.get("id")),
                "label": str(p.get("name") or "宠物档案"),
                "locator": "宠物档案",
            }
            for p in pets
            if p.get("id") is not None
        ],
    }


async def get_health_summary(args: PetScopedArgs, ctx: ToolContext) -> dict[str, Any]:
    pet_id = _pet_id(args, ctx)
    if not pet_id:
        return {"ok": False, "code": "missing_pet", "error": "缺少 pet_id：先确认要查看哪只宠物"}

    dashboard = await ctx.backend.get("/health/dashboard", {"petId": pet_id})
    weekly = await ctx.backend.get("/health/record/weekly", {"petId": pet_id}) or []
    return {
        "ok": True,
        "pet_id": pet_id,
        "dashboard": dashboard,
        "weekly": weekly,
        "citations": [
            {"kind": "health", "id": pet_id, "label": "健康看板", "locator": f"petId={pet_id}"}
        ],
    }


async def search_logs(args: SearchLogsArgs, ctx: ToolContext) -> dict[str, Any]:
    payload = {
        "petId": _pet_id(args, ctx),
        "searchText": (args.keyword or "").strip() or None,
        "current": 1,
        "pageSize": args.limit,
    }
    page = await ctx.backend.post("/log/list/page/vo", payload) or {}
    records = page.get("records") or []
    items = [
        {
            "id": str(r.get("id")),
            "title": r.get("title"),
            "type": r.get("type"),
            "content": (r.get("content") or "")[:200],
            "create_time": r.get("createTime") or r.get("create_time"),
        }
        for r in records
    ]
    return {
        "ok": True,
        "items": items,
        "citations": [
            {
                "kind": "log",
                "id": it["id"],
                "label": str(it["title"] or "生活记录"),
                "locator": str(it["create_time"] or ""),
            }
            for it in items
            if it["id"]
        ],
    }


def build_registry(*, docs: Any = None) -> ToolRegistry:
    registry = ToolRegistry()
    if docs is not None:
        from .docs import search_docs_spec

        registry.register(search_docs_spec())
    registry.register(
        ToolSpec(
            name="get_pet_profile",
            description="读取当前用户的宠物档案（品种、年龄、体重、绝育状态等）。不传 pet_id 时返回全部宠物。",
            args_model=PetScopedArgs,
            handler=get_pet_profile,
            tags=frozenset({"read", "pet"}),
        )
    )
    registry.register(
        ToolSpec(
            name="get_health_summary",
            description="读取某只宠物的健康看板与最近 7 天健康记录（心率/睡眠/步数/体重等）。",
            args_model=PetScopedArgs,
            handler=get_health_summary,
            tags=frozenset({"read", "health"}),
        )
    )
    registry.register(
        ToolSpec(
            name="search_logs",
            description="按关键词搜索宠物的生活记录（喂养、疫苗、就医、洗澡等），返回最近的若干条。",
            args_model=SearchLogsArgs,
            handler=search_logs,
            tags=frozenset({"read", "log"}),
        )
    )
    return registry


__all__ = [
    "PetScopedArgs",
    "SearchLogsArgs",
    "ValidationError",
    "build_registry",
    "get_health_summary",
    "get_pet_profile",
    "search_logs",
]
