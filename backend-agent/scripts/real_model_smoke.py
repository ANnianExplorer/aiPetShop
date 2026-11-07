"""A1 真实模型冒烟：用真 key 跑 L1 + L2，量首 token 延迟与 token 用量。

为什么要单独一个脚本，而不是"手动 curl 一下"：
- curl 看不到「首 token 时刻」，而 P95 首 token 是这条链路上用户唯一能感知的指标；
- 只有真模型才知道我们喂的工具 schema 它认不认、`search_logs` 到底会不会被调用；
- 结果要能复跑：同一台机器、同一组问题，数字可比。

用法（服务需已用真 key 启动在 8099）：

    .\\.venv\\Scripts\\python -m scripts.real_model_smoke
    .\\.venv\\Scripts\\python -m scripts.real_model_smoke --rounds 5 --token token-1001

退出码：0 = 全部通过；1 = 有不满足项（会打印明细）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_BASE = os.getenv("PET_AGENT_SMOKE_BASE", "http://127.0.0.1:8099")
L1_QUESTION = "用一句话介绍你自己，不要超过 30 个字。"
L2_QUESTION = "上次打疫苗是什么时候？"


@dataclass
class Turn:
    question: str
    route: str = ""
    first_token_ms: int = 0
    total_ms: int = 0
    answer: str = ""
    tools: list[str] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    error: str = ""


async def run_turn(client: httpx.AsyncClient, token: str, question: str) -> Turn:
    turn = Turn(question=question)
    started = time.perf_counter()
    async with client.stream(
        "POST",
        "/agent/chat",
        json={"message": question, "channel": "app"},
        headers={"satoken": token},
        timeout=httpx.Timeout(120.0, connect=10.0),
    ) as response:
        if response.status_code != 200:
            body = (await response.aread()).decode("utf-8", "replace")[:300]
            turn.error = f"HTTP {response.status_code}: {body}"
            return turn

        event_name = ""
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                event_name = line[7:]
                continue
            if not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            if event_name == "route":
                turn.route = payload.get("route", "")
            elif event_name == "tool":
                turn.tools.append(payload.get("name", ""))
            elif event_name == "delta":
                if not turn.first_token_ms:
                    turn.first_token_ms = int((time.perf_counter() - started) * 1000)
                turn.answer += payload.get("text", "")
            elif event_name == "done":
                turn.total_ms = int((time.perf_counter() - started) * 1000)
                turn.answer = payload.get("answer") or turn.answer
                turn.citations = payload.get("citations") or []
                usage = payload.get("usage") or {}
                turn.usage = {
                    "prompt": int(usage.get("prompt_tokens") or 0),
                    "completion": int(usage.get("completion_tokens") or 0),
                }
            elif event_name == "error":
                turn.error = f"{payload.get('code')}: {payload.get('message')}"
    return turn


def percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(ratio * (len(ordered) - 1))))
    return ordered[index]


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--token", default=os.getenv("PET_AGENT_SMOKE_TOKEN", "token-1001"))
    parser.add_argument("--rounds", type=int, default=3, help="L1 轮数（用于算 P95 首 token）")
    args = parser.parse_args(argv)

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))

    async with httpx.AsyncClient(base_url=args.base) as client:
        health = (await client.get("/healthz", timeout=10)).json()
        check(
            "模型已配置",
            bool(health.get("model_configured")),
            f"repo={health.get('repo')} model={health.get('model')}",
        )
        check(
            "不是本地桩",
            health.get("model") not in {None, "stub", "scripted"},
            f"model={health.get('model')}",
        )

        l1_turns: list[Turn] = []
        for _ in range(max(1, args.rounds)):
            turn = await run_turn(client, args.token, L1_QUESTION)
            l1_turns.append(turn)
            await asyncio.sleep(0.3)

        l1_ok = [t for t in l1_turns if not t.error]
        check("L1 全部成功", len(l1_ok) == len(l1_turns), f"{len(l1_ok)}/{len(l1_turns)}")
        check(
            "L1 走直答路由",
            all(t.route == "L1" for t in l1_ok),
            ",".join(sorted({t.route for t in l1_ok})),
        )
        check(
            "L1 不调工具",
            all(not t.tools for t in l1_ok),
            ",".join(sorted({tool for t in l1_ok for tool in t.tools})) or "none",
        )
        check(
            "L1 有真实回答",
            all(len(t.answer.strip()) >= 2 for t in l1_ok),
            f"min_chars={min((len(t.answer.strip()) for t in l1_ok), default=0)}",
        )
        check(
            "L1 有 token 计量",
            all(t.usage.get("prompt", 0) > 0 for t in l1_ok),
            f"usage={[t.usage for t in l1_ok]}",
        )

        l2 = await run_turn(client, args.token, L2_QUESTION)
        check("L2 无错误", not l2.error, l2.error or "ok")
        check("L2 走工具路由", l2.route in {"L2", "L3"}, f"route={l2.route}")
        check("L2 调用了 search_logs", "search_logs" in l2.tools, ",".join(l2.tools) or "none")
        check("L2 带引用", bool(l2.citations), json.dumps(l2.citations[:2], ensure_ascii=False))
        check(
            "L2 引用指向记录 7001",
            any(str(c.get("id")) == "7001" for c in l2.citations),
            ",".join(str(c.get("id")) for c in l2.citations),
        )
        check(
            "L2 token 大于 L1（多了一轮工具）",
            l2.usage.get("prompt", 0) > statistics.median([t.usage.get("prompt", 0) for t in l1_ok] or [0]),
            f"l2={l2.usage} l1_median={statistics.median([t.usage.get('prompt', 0) for t in l1_ok] or [0]):.0f}",
        )

    first_tokens = [t.first_token_ms for t in l1_ok if t.first_token_ms]
    summary = {
        "model": health.get("model"),
        "rounds": len(l1_turns),
        "l1_first_token_ms": first_tokens,
        "l1_p50_ms": percentile(first_tokens, 0.50),
        "l1_p95_ms": percentile(first_tokens, 0.95),
        "l1_answers": [t.answer for t in l1_ok],
        "l1_usage": [t.usage for t in l1_ok],
        "l2": {
            "route": l2.route,
            "tools": l2.tools,
            "citations": l2.citations,
            "answer": l2.answer,
            "usage": l2.usage,
            "first_token_ms": l2.first_token_ms,
            "total_ms": l2.total_ms,
            "error": l2.error,
        },
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    passed = sum(1 for _, ok, _ in checks if ok)
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    print(f"{passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
