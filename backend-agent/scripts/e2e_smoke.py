"""真进程冒烟：对着已启动的 services 做一次端到端验收。

前置（三个进程）：
    uvicorn tests.stub_java:app --port 8097
    uvicorn tests.stub_llm:app  --port 8098
    uvicorn app.main:app        --port 8099   （env 指向上面两个）

跑：
    .venv\\Scripts\\python -m scripts.e2e_smoke

检查项：
1. /healthz 就绪；
2. L1 闲聊：route=L1，事件顺序合法，无工具事件；
3. L2 记录类：真的调用了 search_logs，done 里带 citation（7001）；
4. 续传：全量事件、?after=N、Last-Event-ID 三种方式拿到同一批事件；
5. 回读：/agent/sessions/{id}/messages 里有 user/assistant 两条；
6. 越权：换一个 token 读别人的会话 → 404。
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Iterator

import httpx

BASE = "http://127.0.0.1:8099"
TOKEN = "token-1001"


@dataclass
class Result:
    name: str
    ok: bool
    note: str = ""


def events(response: httpx.Response) -> list[dict[str, Any]]:
    """把 SSE 文本切成 [{id, event, data}]。"""
    parsed: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in response.text.splitlines():
        if line.startswith("id:"):
            current["id"] = int(line[3:].strip())
        elif line.startswith("event:"):
            current["event"] = line[6:].strip()
        elif line.startswith("data:"):
            current["data"] = json.loads(line[5:].strip())
        elif not line.strip() and current:
            parsed.append(current)
            current = {}
    return parsed


def chat(client: httpx.Client, message: str, session_id: str | None = None) -> httpx.Response:
    payload: dict[str, Any] = {"message": message, "channel": "app"}
    if session_id:
        payload["session_id"] = session_id
    return client.post(
        "/agent/chat", json=payload, headers={"satoken": TOKEN}, timeout=30
    )


def main() -> int:
    results: list[Result] = []
    with httpx.Client(base_url=BASE, timeout=30) as client:
        health = client.get("/healthz").json()
        results.append(
            Result("healthz", health.get("status") == "ok" and health.get("graph_ready"), str(health))
        )

        # ---- L1
        r1 = chat(client, "你好")
        e1 = events(r1)
        names1 = [e["event"] for e in e1]
        session_id = e1[0]["data"]["session_id"] if e1 else ""
        results.append(
            Result(
                "L1 事件序列",
                names1[0] == "route" and names1[-1] == "done" and "tool" not in names1,
                " -> ".join(names1),
            )
        )
        results.append(
            Result("L1 路由", e1[0]["data"]["route"] == "L1" if e1 else False, str(e1[0]["data"])[:120])
        )

        # ---- L2
        r2 = chat(client, "上次疫苗是什么时候", session_id)
        e2 = events(r2)
        names2 = [e["event"] for e in e2]
        done = next((e["data"] for e in e2 if e["event"] == "done"), {})
        tools = [e["data"]["name"] for e in e2 if e["event"] == "tool"]
        results.append(
            Result("L2 路由", e2 and e2[0]["data"]["route"] == "L2", str(e2[0]["data"])[:120] if e2 else "")
        )
        results.append(Result("L2 调用工具", tools == ["search_logs"], str(tools)))
        results.append(
            Result(
                "L2 引用可点回",
                bool(done.get("citations")) and done["citations"][0]["id"] == "7001",
                json.dumps(done.get("citations"), ensure_ascii=False)[:160],
            )
        )
        results.append(
            Result(
                "L2 用量已结算",
                (done.get("usage") or {}).get("prompt_tokens", 0) > 0,
                json.dumps(done.get("usage"), ensure_ascii=False),
            )
        )
        run_id = done.get("run_id", "")

        # ---- 续传：三种方式等价
        full = events(client.get(f"/agent/runs/{run_id}/events", headers={"satoken": TOKEN}))
        after = events(
            client.get(f"/agent/runs/{run_id}/events?after=2", headers={"satoken": TOKEN})
        )
        resume = events(
            client.get(
                f"/agent/runs/{run_id}/events",
                headers={"satoken": TOKEN, "Last-Event-ID": "2"},
            )
        )
        results.append(
            Result(
                "续传等价",
                [e["id"] for e in after] == [e["id"] for e in resume] == [e["id"] for e in full if e["id"] > 2],
                f"full={len(full)} after={len(after)} resume={len(resume)}",
            )
        )

        # ---- 回读
        body = client.get(
            f"/agent/sessions/{session_id}/messages", headers={"satoken": TOKEN}
        ).json()
        rows = body.get("messages") or []
        roles = [m["role"] for m in rows]
        results.append(
            Result(
                "会话回读",
                len(rows) == 4 and roles[:2] == ["user", "assistant"],
                f"{len(rows)} 条 / {roles}",
            )
        )

        # ---- 越权
        other = client.get(
            f"/agent/sessions/{session_id}/messages", headers={"satoken": "token-9999"}
        )
        results.append(Result("越权被拒", other.status_code in (401, 403, 404), str(other.status_code)))

    width = max(len(r.name) for r in results)
    for r in results:
        print(f"[{'PASS' if r.ok else 'FAIL'}] {r.name.ljust(width)}  {r.note}")
    failed = [r for r in results if not r.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
