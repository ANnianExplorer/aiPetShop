"""评测 runner：把「凭感觉觉得对」变成「有阈值、可回归的数字」。

借鉴 claw-eval 的三件事（其余不抄）：
1. 用例是数据（`cases.jsonl`），不是散落在测试里的断言；
2. 每条用例有明确 expect，通过/失败逐条落报告；
3. 有硬阈值，低于阈值进程退出码非 0 —— 才能进 CI。

三个套件都不需要真模型：
- routing：确定性分类器命中率；
- safety：工具网关对越权/超范围的拒绝率（必须 100%）；
- memory：多轮对话的落库与回放完整性。

用法：
    python -m evals.run                 # 全部套件
    python -m evals.run --suite routing
    python -m evals.run --json          # 机器可读结果
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx
from app.config import Settings
from app.domain.models import ToolResult
from app.storage import InMemoryRepository
from app.tools import (
    BackendClient,
    ToolContext,
    ToolGateway,
    ToolPolicy,
    build_registry,
)
from app.domain.router import classify

CASES_PATH = Path(__file__).with_name("cases.jsonl")
REPORT_DIR = Path(__file__).with_name("reports")

# 阈值：安全类不允许任何放水；其余允许少量抖动
THRESHOLDS: dict[str, float] = {"routing": 0.95, "safety": 1.0, "memory": 1.0}

JAVA_ROUTES: dict[str, Any] = {
    "/api/v1/pet/list": [{"id": "5001", "name": "Lumina"}],
    "/api/v1/pet/get/vo": {"id": "5001", "name": "Lumina"},
    "/api/v1/health/dashboard": {"petId": "5001", "heartRate": 92},
    "/api/v1/health/record/weekly": [],
    "/api/v1/log/list/page/vo": {"records": [], "total": 0},
}


def _java(request: httpx.Request) -> httpx.Response:
    data = JAVA_ROUTES.get(request.url.path)
    if data is None:
        return httpx.Response(404, json={"code": 40400, "message": "unknown"})
    return httpx.Response(200, json={"code": 0, "data": data})


def _http() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(_java))


@dataclass
class CaseResult:
    id: str
    suite: str
    passed: bool
    expected: dict[str, Any]
    actual: dict[str, Any] = field(default_factory=dict)
    note: str = ""


@dataclass
class SuiteReport:
    name: str
    total: int
    passed: int

    @property
    def rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def threshold(self) -> float:
        return THRESHOLDS.get(self.name, 1.0)


# --------------------------------------------------------------------- 套件
def run_routing(case: dict[str, Any]) -> CaseResult:
    decision = classify(case["question"])
    expected = case["expect"]
    actual = {"route": decision.route.value, "intent": decision.intent.value}
    ok = all(actual.get(k) == v for k, v in expected.items())
    return CaseResult(case["id"], "routing", ok, expected, actual, decision.reason)


async def run_safety(case: dict[str, Any]) -> CaseResult:
    gateway = ToolGateway(build_registry(), ToolPolicy(), max_calls_per_run=4)
    ctx = ToolContext(
        user_id="1001",
        token="token",
        run_id=f"eval-{case['id']}",
        backend=BackendClient("http://java/api/v1", "token", _http()),
        pet_id="5001",
        auto_commit=False,
    )
    result: ToolResult = await gateway.invoke(case["tool"], case["args"], ctx, "app")
    expected = case["expect"]
    actual = {"ok": result.ok, "code": result.code}
    ok = all(actual.get(k) == v for k, v in expected.items())
    return CaseResult(case["id"], "safety", ok, expected, actual, (result.error or "")[:80])


async def run_memory(case: dict[str, Any]) -> CaseResult:
    from app.api import create_app
    from app.llm import ScriptedModel

    settings = Settings(
        env="test", llm_api_key="test", auth_mode="header", repo_backend="memory"
    )
    repo = InMemoryRepository()
    app = create_app(settings, model=ScriptedModel(), repo=repo, http_client=_http())

    session_id: str | None = None
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as client:
        for turn in case["turns"]:
            payload: dict[str, Any] = {"message": turn}
            if session_id:
                payload["session_id"] = session_id
            response = await client.post(
                "/agent/chat",
                json=payload,
                headers={"satoken": "t", "x-user-id": "1001"},
            )
            for block in response.text.split("\n\n"):
                if "event: route" in block:
                    session_id = json.loads(block.split("data: ", 1)[1])["session_id"]

        expected_turns = int(case["expect"]["turns_recorded"])
        history = await repo.history(session_id or "", 50)
        contents = [h["content"] for h in history]
        recorded = len([c for c in contents if c in case["turns"]])
        ok = recorded == expected_turns and len(contents) == expected_turns * 2
        actual = {"recorded_turns": recorded, "messages": len(contents)}
    return CaseResult(
        case["id"], "memory", ok, {"turns_recorded": expected_turns}, actual
    )


RUNNERS: dict[str, Callable[[dict[str, Any]], CaseResult | Awaitable[CaseResult]]] = {
    "routing": run_routing,
    "safety": run_safety,
    "memory": run_memory,
}


def load_cases(suite: str | None) -> list[dict[str, Any]]:
    cases = [
        json.loads(line)
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [c for c in cases if suite in (None, "all", c["suite"])]


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Pet-Agent 评测")
    parser.add_argument("--suite", default="all", choices=["all", *RUNNERS])
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args(argv)

    results: list[CaseResult] = []
    for case in load_cases(args.suite):
        runner = RUNNERS[case["suite"]]
        produced = runner(case)
        results.append(await produced if hasattr(produced, "__await__") else produced)

    suites: dict[str, SuiteReport] = {}
    for suite in sorted({r.suite for r in results}):
        rows = [r for r in results if r.suite == suite]
        suites[suite] = SuiteReport(suite, len(rows), sum(1 for r in rows if r.passed))

    failed = [s for s in suites.values() if s.rate < s.threshold]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suites": [
            {
                "name": s.name,
                "total": s.total,
                "passed": s.passed,
                "rate": round(s.rate, 4),
                "threshold": s.threshold,
                "ok": s.rate >= s.threshold,
            }
            for s in suites.values()
        ],
        "failures": [asdict(r) for r in results if not r.passed],
    }

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for s in suites.values():
            mark = "PASS" if s.rate >= s.threshold else "FAIL"
            print(f"[{mark}] {s.name:<8} {s.passed}/{s.total} = {s.rate:.0%} (阈值 {s.threshold:.0%})")
        for r in results:
            if not r.passed:
                print(f"  - {r.id}: expected={r.expected} actual={r.actual} {r.note}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
