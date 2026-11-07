"""P2 幂等冒烟：直接打真进程，验证「同一条消息重试两次只执行一次」。

和单测的区别：这里走的是真 HTTP、真 MySQL、真 Redis（如果开了），
所以能抓到「内存实现同意、真实现不同意」这类问题——S1.8 D1（RESP3 握手）
就是这么抓到的。

用法：
    .venv\\Scripts\\python.exe -m scripts.idempotency_smoke
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE = os.environ.get("AGENT_BASE", "http://127.0.0.1:8099")
TOKEN = os.environ.get("AGENT_TOKEN", "token-1001")


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""


def _request(
    method: str, path: str, body: dict | None = None, *, token: str | None = TOKEN
) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("satoken", token)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def _sse(text: str) -> list[dict]:
    """把 SSE 文本解析成 [{event, data}]，只关心事件名和 data。"""
    events: list[dict] = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        name, payload = "message", []
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                payload.append(line[5:].strip())
        if payload:
            events.append({"event": name, "data": json.loads("\n".join(payload))})
    return events


def _done(events: list[dict]) -> dict:
    done = [e["data"] for e in events if e["event"] == "done"]
    assert done, f"没有 done 事件：{[e['event'] for e in events]}"
    return done[-1]


def main() -> int:
    results: list[Result] = []

    def check(name: str, fn) -> None:
        try:
            detail = fn()
            results.append(Result(name, True, str(detail)))
        except Exception as exc:
            results.append(Result(name, False, f"{type(exc).__name__}: {exc}"))

    key = f"smoke-{int(time.time())}"
    box: dict = {}

    def health() -> str:
        status, text = _request("GET", "/healthz", token=None)
        assert status == 200, f"{status} {text}"
        body = json.loads(text)
        return f"repo={body.get('repo')} tools={len(body.get('tools') or [])}"

    def first_send() -> str:
        status, text = _request(
            "POST", "/agent/chat", {"message": "上次打疫苗是什么时候", "client_message_id": key}
        )
        assert status == 200, f"{status} {text}"
        done = _done(_sse(text))
        assert "replayed" not in done, "首次执行不该被标记成回放"
        box["run_id"] = done["run_id"]
        box["session_id"] = done["session_id"]
        return f"run={done['run_id']} answer={done['answer'][:16]}"

    def retry_same_key() -> str:
        status, text = _request(
            "POST", "/agent/chat", {"message": "上次打疫苗是什么时候", "client_message_id": key}
        )
        assert status == 200, f"{status} {text}"
        done = _done(_sse(text))
        assert done["run_id"] == box["run_id"], "重试应该命中同一个 run"
        assert done.get("replayed") is True, f"重试应标记 replayed，实际 {done}"
        return f"replayed run={done['run_id']}"

    def only_one_execution() -> str:
        status, text = _request("GET", f"/agent/sessions/{box['session_id']}/messages")
        assert status == 200, f"{status} {text}"
        messages = json.loads(text)["messages"]
        roles = [m["role"] for m in messages if m["role"] in ("user", "assistant")]
        assert roles.count("user") == 1, f"用户消息应该只有 1 条，实际 {roles}"
        assert roles.count("assistant") == 1, f"助手消息应该只有 1 条，实际 {roles}"
        return f"messages={len(messages)} roles={roles}"

    def replay_events_available() -> str:
        status, text = _request("GET", f"/agent/runs/{box['run_id']}/events")
        assert status == 200, f"{status} {text}"
        events = _sse(text)
        names = [e["event"] for e in events]
        assert "done" in names, f"事件流的 run 应该能回放，实际 {names}"
        return f"replayed={len(names)} events"

    def different_key_runs_again() -> str:
        status, text = _request(
            "POST", "/agent/chat", {"message": "上次打疫苗是什么时候", "client_message_id": key + "-b"}
        )
        assert status == 200, f"{status} {text}"
        done = _done(_sse(text))
        assert done["run_id"] != box["run_id"], "不同 key 必须是新的 run"
        return f"run={done['run_id']}"

    def usage_counts_two_runs() -> str:
        status, text = _request("GET", "/agent/usage/me?days=7")
        assert status == 200, f"{status} {text}"
        body = json.loads(text)
        assert body["runs"] >= 2, f"应该至少 2 次执行，实际 {body}"
        return f"runs={body['runs']} tokens={body['total_tokens']}"

    def bad_key_rejected() -> str:
        status, text = _request(
            "POST", "/agent/chat", {"message": "hi", "client_message_id": "带空格 key"}
        )
        assert status == 422, f"非法 key 应被 422 拦下，实际 {status} {text}"
        return "422"

    check("healthz 可用", health)
    check("首次发送成功", first_send)
    check("同 key 重试命中同一 run", retry_same_key)
    check("只执行一次（消息不翻倍）", only_one_execution)
    check("事件日志可回放", replay_events_available)
    check("不同 key 各自执行", different_key_runs_again)
    check("用量只记两次执行", usage_counts_two_runs)
    check("非法幂等键被拒", bad_key_rejected)

    failed = [r for r in results if not r.ok]
    for item in results:
        print(f"[{'PASS' if item.ok else 'FAIL'}] {item.name} → {item.detail}")
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
