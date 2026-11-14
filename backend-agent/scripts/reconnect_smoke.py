"""断线重连冒烟：真 uvicorn + 真 socket，验证「客户端掐断连接后 run 照样跑完」。

和单测的区别：单测用 ASGITransport，断连是"协程被 cancel"；这里是真的 TCP 断开，
走的是 uvicorn 的 disconnect 语义——最接近手机切网络/进电梯的真实场景。

做法：
1. 进程内起一个 uvicorn（注入 0.4s/片 的慢模型，保证能在流中间断开）；
2. 客户端 A 读两片就 hard close 掉 socket；
3. 等 run 在后台跑完，客户端 B 用 `?follow=1&after=<已收最大 id>` 接回来；
4. 断言：run 最终有 done、id 严格递增不重不漏、两段文本拼起来正好是完整回答。

用法：
    .venv\\Scripts\\python.exe -m scripts.reconnect_smoke
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from http.client import HTTPConnection

import uvicorn

from app.api.app import create_app
from app.config import Settings
from app.domain.models import Usage
from app.llm.base import StreamChunk
from app.llm.fake import ScriptedModel

HOST = "127.0.0.1"
PORT = 8123
TOKEN = "token-1001"
USER = "1001"
CHUNKS = ("第一段", "第二段", "第三段")


class SlowModel(ScriptedModel):
    """每片之间喘口气，好让客户端有机会在半路把连接掐了。"""

    def __init__(self, delay_s: float = 0.4, chunks: tuple[str, ...] = CHUNKS) -> None:
        super().__init__(chunks=chunks, usage=Usage(12, 6))
        self._delay = delay_s

    async def stream(self, messages: list[dict]) -> AsyncIterator[StreamChunk]:  # type: ignore[override]
        self.stream_calls.append([dict(m) for m in messages])
        for index, chunk in enumerate(CHUNKS):
            if index:
                await asyncio.sleep(self._delay)
            yield StreamChunk(text=chunk)
        yield StreamChunk(usage=Usage(12, 6))


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def parse_sse(lines: list[str]) -> list[dict]:
    """把若干 `event:`/`data:` 行解析成 [{event, data, id}]。"""
    events: list[dict] = []
    name, seq, payload = "message", None, []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            if payload:
                events.append({"event": name, "data": json.loads("\n".join(payload)), "id": seq})
            name, seq, payload = "message", None, []
            continue
        if line.startswith("event:"):
            name = line[6:].strip()
        elif line.startswith("id:"):
            try:
                seq = int(line[3:].strip())
            except ValueError:
                seq = None
        elif line.startswith("data:"):
            payload.append(line[5:].strip())
    if payload:
        events.append({"event": name, "data": json.loads("\n".join(payload)), "id": seq})
    return events


def _headers(*, stream_close: bool = False) -> dict[str, str]:
    headers = {"satoken": TOKEN, "x-user-id": USER, "accept": "text/event-stream"}
    if stream_close:
        # 不要 keep-alive：读完就让服务端关连接，客户端 readlines 才能立刻收到 EOF
        headers["connection"] = "close"
    return headers


def read_until(conn: HTTPConnection, stop_after: int) -> tuple[list[str], dict | None]:
    """逐行读 SSE，凑够 stop_after 个事件就返回；返回 (行, route 的 data)。"""
    handle = conn.getresponse()
    stream = handle.fp
    assert stream is not None
    lines: list[str] = []
    events: list[dict] = []
    while len(events) < stop_after:
        raw = stream.readline()
        if not raw:
            break
        text = raw.decode("utf-8")
        lines.append(text)
        if text.strip() == "":
            events = parse_sse(lines)
    return lines, (events[0]["data"] if events else None)


def open_chat() -> tuple[HTTPConnection, list[str], dict]:
    conn = HTTPConnection(HOST, PORT, timeout=30)
    body = json.dumps({"message": "你好"})
    headers = dict(_headers(), **{"content-type": "application/json"})
    conn.request("POST", "/agent/chat", body=body, headers=headers)
    lines, route = read_until(conn, 2)  # route + 第一片 delta
    assert route is not None, f"没拿到 route 事件，前几行：{lines[:6]}"
    return conn, lines, route


def follow(run_id: str, after: int) -> tuple[HTTPConnection, list[str]]:
    conn = HTTPConnection(HOST, PORT, timeout=30)
    conn.request("GET", f"/agent/runs/{run_id}/events?after={after}&follow=1", headers=_headers(stream_close=True))
    handle = conn.getresponse()
    stream = handle.fp
    assert stream is not None
    lines = [line.decode("utf-8") for line in stream.readlines()]
    return conn, lines


def run_checks() -> list[Check]:
    checks: list[Check] = []

    conn, head_lines, route = open_chat()
    head_events = parse_sse(head_lines)
    run_id = route["run_id"]
    cursor = max(e["id"] or 0 for e in head_events)
    head_text = "".join(str(e["data"].get("text", "")) for e in head_events if e["event"] == "delta")
    conn.close()  # 真·掐线：不发任何结束标记

    # 只等一小会儿就重连：此刻后台才跑到第二片，follow 必须挂住等到终态
    time.sleep(0.15)

    started = time.monotonic()
    _conn, tail_lines = follow(run_id, cursor)
    waited_ms = (time.monotonic() - started) * 1000
    tail_events = parse_sse(tail_lines)
    tail_text = "".join(str(e["data"].get("text", "")) for e in tail_events if e["event"] == "delta")
    done = tail_events[-1] if tail_events else None

    checks.append(
        Check(
            "掐线后 run 仍然走到 done",
            done is not None and done["event"] == "done",
            f"最后一条事件 = {done['event'] if done else '无'}",
        )
    )
    checks.append(
        Check(
            "重连时 run 还在跑：follow 挂住等到终态",
            bool(done is not None and done["event"] == "done") and waited_ms >= 100,
            f"等了 {waited_ms:.0f} ms 才收到 done",
        )
    )
    ids = [e["id"] for e in tail_events if e["id"] is not None]
    checks.append(
        Check(
            "续传 id 严格递增且都大于游标",
            ids == sorted(ids) and len(set(ids)) == len(ids) and bool(ids) and ids[0] > cursor,
            f"cursor={cursor} 续传 ids={ids}",
        )
    )
    answer = str((done["data"].get("answer") if done else "") or "")
    checks.append(
        Check(
            "两段文本拼起来正好是完整回答（不重不漏）",
            bool(answer) and head_text + tail_text == answer,
            f"{head_text!r} + {tail_text!r} vs {answer!r}",
        )
    )

    snapshot_conn = HTTPConnection(HOST, PORT, timeout=30)
    snapshot_conn.request("GET", f"/agent/runs/{run_id}/events?after={cursor}", headers=_headers(stream_close=True))
    snapshot_lines = [line.decode("utf-8") for line in snapshot_conn.getresponse().fp.readlines()]
    snapshot_events = parse_sse(snapshot_lines)
    snapshot_conn.close()
    checks.append(
        Check(
            "不带 follow 的快照语义不变（拿到同一份尾巴）",
            [e["id"] for e in snapshot_events] == ids,
            f"snapshot ids={[e['id'] for e in snapshot_events]}",
        )
    )
    return checks


def main() -> int:
    settings = Settings(
        env="test",
        llm_api_key="test-key",
        llm_model="scripted",
        auth_mode="header",
        repo_backend="memory",
    )
    application = create_app(settings, model=SlowModel(delay_s=0.4))
    config = uvicorn.Config(application, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    else:
        print("FAIL 服务没起来")
        return 1

    try:
        checks = run_checks()
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    passed = sum(1 for check in checks if check.ok)
    for check in checks:
        print(f"{'PASS' if check.ok else 'FAIL'} {check.name} — {check.detail}")
    print(f"{passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
