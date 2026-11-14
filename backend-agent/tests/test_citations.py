"""引用回跳（BACKLOG C4）：`citation.locator` 必须是 App 内路由，前端才能直接 push。

这条契约放在工具层测，比走整条 SSE 更直接：引用是工具产出的，坏在源头就只能在源头拦住。
"""

from __future__ import annotations

from typing import Any

from conftest import JAVA_LOG_PAGE, JAVA_PET

from app.tools.pet import (
    PetScopedArgs,
    SearchLogsArgs,
    SearchPostsArgs,
    _fmt_date,
    get_health_summary,
    get_pet_profile,
    search_logs,
    search_posts,
)
from app.tools.spec import ToolContext

POST_PAGE: dict[str, Any] = {
    "records": [
        {
            "id": "9001",
            "content": "换粮第三天终于不软便了，记录一下",
            "category": "daily",
            "createTime": "2026-11-10 20:11:00",
        }
    ],
    "total": 1,
}


class FakeBackend:
    """只回放固定响应，不碰网络；顺手记下调用参数供断言。"""

    def __init__(self, routes: dict[str, Any]) -> None:
        self._routes = routes
        self.calls: list[tuple[str, str, Any]] = []

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("GET", path, params))
        return self._routes.get(path)

    async def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append(("POST", path, payload))
        return self._routes.get(path)


def make_ctx(routes: dict[str, Any], *, pet_id: str | None = "5001") -> ToolContext:
    return ToolContext(
        user_id="1001",
        token="token-1001",
        run_id="run-1",
        backend=FakeBackend(routes),  # type: ignore[arg-type]
        pet_id=pet_id,
    )


def _routes() -> dict[str, Any]:
    return {
        "/pet/list": [JAVA_PET],
        "/pet/get/vo": JAVA_PET,
        "/health/dashboard": {"petId": "5001", "heartRate": 92},
        "/health/record/weekly": [
            {"date": "2026-11-05", "steps": 3200},
            {"date": "2026-11-09", "steps": 6100},
            {"date": "2026-11-07", "steps": 4400},
        ],
        "/log/list/page/vo": JAVA_LOG_PAGE,
        "/post/list/page/vo": POST_PAGE,
    }


async def test_pet_citation_points_to_pet_detail() -> None:
    result = await get_pet_profile(PetScopedArgs(), make_ctx(_routes()))
    assert [c["locator"] for c in result["citations"]] == ["/pet-detail/5001"]


async def test_health_citation_carries_latest_week_date() -> None:
    """跳到「那一周里最近的一天」，不是今天：引用的是历史数据，跳今天会找不到。"""
    result = await get_health_summary(PetScopedArgs(), make_ctx(_routes()))
    assert [c["locator"] for c in result["citations"]] == [
        "/weekly-health-detail?petId=5001&date=2026-11-09"
    ]


async def test_health_citation_without_weekly_has_no_date() -> None:
    routes = _routes()
    routes["/health/record/weekly"] = []
    result = await get_health_summary(PetScopedArgs(), make_ctx(routes))
    assert [c["locator"] for c in result["citations"]] == ["/weekly-health-detail?petId=5001"]


async def test_log_citation_points_to_log_detail() -> None:
    result = await search_logs(SearchLogsArgs(keyword="疫苗"), make_ctx(_routes()))
    assert [c["locator"] for c in result["citations"]] == ["/log/7001"]


async def test_post_citation_points_to_post_detail() -> None:
    ctx = make_ctx(_routes())
    result = await search_posts(SearchPostsArgs(keyword="换粮"), ctx)
    citations = result["citations"]
    assert [c["kind"] for c in citations] == ["post"]
    assert [c["locator"] for c in citations] == ["/post/9001"]
    # label 是正文摘要，用户点之前能看出这是哪一条
    assert citations[0]["label"].startswith("换粮第三天")
    assert ("POST", "/post/list/page/vo", {"searchText": "换粮", "current": 1, "pageSize": 3}) in ctx.backend.calls  # type: ignore[attr-defined]


async def test_every_locator_is_an_app_route() -> None:
    """一条总闸：新增工具忘了写 `locator` 或者写成「宠物档案」这种给人看的话，这里会红。"""
    routes = _routes()
    ctx = make_ctx(routes)
    produced = [
        (await get_pet_profile(PetScopedArgs(), ctx))["citations"],
        (await get_health_summary(PetScopedArgs(), ctx))["citations"],
        (await search_logs(SearchLogsArgs(), ctx))["citations"],
        (await search_posts(SearchPostsArgs(), ctx))["citations"],
    ]
    locators = [c["locator"] for group in produced for c in group]
    assert locators, "四个工具一条引用都没产出，检查夹具"
    assert all(loc.startswith("/") for loc in locators), locators


def test_java_date_normalises_both_shapes() -> None:
    """Java 侧 `Date` 可能是毫秒时间戳，也可能是 `yyyy-MM-dd HH:mm:ss`，归一后才能塞进 query。"""
    assert _fmt_date("2026-11-05 10:00:00") == "2026-11-05"
    assert _fmt_date("2026-11-05") == "2026-11-05"
    assert _fmt_date(1762300000000) is not None
    assert _fmt_date(None) is None
    assert _fmt_date("") is None
    assert _fmt_date(True) is None
