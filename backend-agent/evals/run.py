"""评测 runner：把「凭感觉觉得对」变成「有阈值、可回归的数字」。

借鉴 claw-eval 的三件事（其余不抄）：
1. 用例是数据（`cases.jsonl`），不是散落在测试里的断言；
2. 每条用例有明确 expect，通过/失败逐条落报告；
3. 有硬阈值，低于阈值进程退出码非 0 —— 才能进 CI。

三个套件都不需要真模型：
- routing：确定性分类器命中率；
- safety：工具网关对越权/超范围的拒绝率（必须 100%）；
- memory：抽取质量（`text`）、服务层隔离与幂等（`observe`）、历史完整性（`turns`）。

`memory` 套件的三种用例形状（见 docs/plans/s1.27-memory-evals.md）：
- `text`  → `extract(text)` 的 key→value 必须**全等** `expect`，`forbid` 的 key 一个都不许出现；
- `observe` → `MemoryService.observe` 跑完后 `pet_id → (key→value)` 必须等于 `expect.pets`，
  可选的 `expect.ops` 按顺序比对 add/update/noop；
- `turns` → 多轮对话落库条数 = 轮数 × 2（原有的管道连通性检查）。

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
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings
from app.domain.models import ToolResult
from app.domain.router import classify
from app.storage import InMemoryRepository
from app.tools import (
    BackendClient,
    ToolContext,
    ToolGateway,
    ToolPolicy,
    build_registry,
)

CASES_PATH = Path(__file__).with_name("cases.jsonl")
REPORT_DIR = Path(__file__).with_name("reports")

# 阈值：安全类不允许任何放水；其余允许少量抖动
THRESHOLDS: dict[str, float] = {"routing": 0.95, "safety": 1.0, "memory": 0.9}

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
    """三条子路径按用例形状分派；`turns` 是原来的落库检查，`text`/`observe` 是 S1.27 新增。"""
    if "text" in case:
        return run_extract(case)
    if "observe" in case:
        return await run_observe(case)
    return await run_history(case)


def run_extract(case: dict[str, Any]) -> CaseResult:
    """纯函数抽取：多抽一个 key 就是假事实，所以判据是集合全等而不是包含。"""
    from app.memory.extract import extract

    facts = {c.key: c.value for c in extract(case["text"])}
    expected: dict[str, str] = case.get("expect") or {}
    forbidden: list[str] = list(case.get("forbid") or [])
    leaked = sorted(key for key in forbidden if key in facts)
    wrong = {
        key: {"want": want, "got": facts.get(key)}
        for key, want in expected.items()
        if facts.get(key) != want
    }
    extra = {key: value for key, value in facts.items() if key not in expected}
    ok = not leaked and not wrong and not extra
    problems: list[str] = []
    if leaked:
        problems.append(f"forbid_leaked={leaked}")
    if wrong:
        problems.append(f"wrong={wrong}")
    if extra:
        problems.append(f"extra={extra}")
    actual: dict[str, Any] = {"facts": facts}
    return CaseResult(
        case["id"], "memory", ok, expected, actual, "; ".join(problems)[:160]
    )


async def run_observe(case: dict[str, Any]) -> CaseResult:
    """服务层：多宠物隔离、重复说幂等、置信度过滤——这三件事是 HTTP 之外的规则。"""
    from app.memory.service import MemoryService

    repo = InMemoryRepository()
    service = MemoryService(repo, min_confidence=float(case.get("min_confidence", 0.7)))
    ops: list[str] = []
    pets: list[str] = []
    for step in case["observe"]:
        pet = step["pet"]
        if pet not in pets:
            pets.append(pet)
        written = await service.observe("1001", pet, step["text"])
        ops.extend(op.value for _fact, op in written)

    expected_pets: dict[str, dict[str, str]] = case["expect"]["pets"]
    actual_pets: dict[str, dict[str, str]] = {}
    for pet in pets:
        rows = await repo.list_memory_facts("1001", pet, 50)
        actual_pets[pet] = {f.key: f.value for f in sorted(rows, key=lambda f: f.key)}

    expected_ops = case["expect"].get("ops")
    problems: list[str] = []
    if actual_pets != expected_pets:
        problems.append(f"pets={actual_pets}")
    if expected_ops is not None and ops != list(expected_ops):
        problems.append(f"ops={ops}")
    return CaseResult(
        case["id"],
        "memory",
        not problems,
        {k: v for k, v in case["expect"].items()},
        {"pets": actual_pets, **({"ops": ops} if expected_ops is not None else {})},
        "; ".join(problems)[:160],
    )


async def run_history(case: dict[str, Any]) -> CaseResult:
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
        "generated_at": datetime.now(UTC).isoformat(),
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
