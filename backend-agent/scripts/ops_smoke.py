"""S1.16 真机冒烟：指标 / 记忆导出删除 / 在途消息巡检回收。

前置（真机形态）：
    uvicorn app.main:app --port 8099
    env: REPO_BACKEND=mysql, MYSQL_DSN=..., EVENT_BACKEND=redis, TASK_BACKEND=redis,
         TASK_SWEEP_INTERVAL_S=2, TASK_VISIBLE_TIMEOUT_S=1, AUTH_MODE=backend,
         LLM_BASE_URL=http://127.0.0.1:8098/v1, LLM_MODEL=stub, BACKEND_BASE_URL=...

用法：python -m scripts.ops_smoke
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
import pymysql
import redis.asyncio as aioredis

AGENT = os.environ.get("PET_AGENT_URL", "http://127.0.0.1:8099")
REDIS_URL = os.environ.get("PET_AGENT_REDIS_URL", "redis://127.0.0.1:6379/0")


def _dsn_parts() -> dict[str, Any]:
    """从 PET_AGENT_MYSQL_DSN（或 PET_AGENT_TEST_MYSQL_DSN）里取库名/账号，避免再写一份口令。"""
    raw = os.environ.get("PET_AGENT_MYSQL_DSN") or os.environ.get("PET_AGENT_TEST_MYSQL_DSN") or ""
    if not raw:
        return {}
    parsed = urlparse(raw)
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/petlumina").lstrip("/"),
    }


MYSQL = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": os.environ.get("PETLUMINA_DB_PASSWORD", ""),
    "database": "petlumina",
    **_dsn_parts(),
}
UID = f"{int(time.time()) % 100000:05d}"
TOKEN = f"token-{UID}"
HEADERS = {"satoken": TOKEN, "x-user-id": UID}


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""
    notes: list[str] = field(default_factory=list)


def check(results: list[Result], name: str, ok: bool, detail: str = "") -> None:
    results.append(Result(name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


async def chat(http: httpx.AsyncClient, message: str) -> dict:
    body = {"message": message, "channel": "app"}
    async with http.stream("POST", "/agent/chat", json=body, headers=HEADERS) as response:
        text = await response.aread()
    events = []
    for block in text.decode("utf-8").strip().split("\n\n"):
        event = {"event": "", "data": {}}
        for line in block.splitlines():
            if line.startswith("event: "):
                event["event"] = line[7:]
            elif line.startswith("data: "):
                event["data"] = json.loads(line[6:])
        if event["event"]:
            events.append(event)
    return {"status": response.status_code, "events": events}


def done_of(payload: dict) -> dict:
    for event in payload["events"]:
        if event["event"] == "done":
            return event["data"]
    return {}


def metric_value(text: str, name: str, **labels: str) -> float:
    pattern = re.compile(rf"^{name}\{{([^}}]*)\}} (\S+)$")
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        pairs = dict(re.findall(r'(\w+)="([^"]*)"', match.group(1)))
        if all(pairs.get(k) == v for k, v in labels.items()):
            return float(match.group(2))
    return 0.0


async def main() -> int:
    results: list[Result] = []
    async with httpx.AsyncClient(base_url=AGENT, timeout=30.0) as http:
        # 1. 健康
        health = (await http.get("/healthz")).json()
        check(results, "healthz 就绪", health.get("status") == "ok", f"tools={health.get('tools')}")

        # 2. /metrics 可读
        metrics = await http.get("/metrics")
        text = metrics.text
        check(
            results,
            "/metrics 文本格式",
            metrics.status_code == 200 and "# TYPE pet_agent_http_requests_total counter" in text,
            f"status={metrics.status_code} bytes={len(text)}",
        )

        # 3. 一轮 L1 对话
        payload = await chat(http, "你好")
        done = done_of(payload)
        check(results, "L1 对话成功", payload["status"] == 200 and bool(done.get("answer")), str(done.get("answer")))

        # 4. 指标真的涨了
        text = (await http.get("/metrics")).text
        runs = metric_value(text, "pet_agent_runs_total", route="L1", status="succeeded")
        prompt = metric_value(text, "pet_agent_tokens_total", direction="prompt")
        check(results, "runs/tokens 有计数", runs >= 1 and prompt >= 1, f"runs={runs} prompt={prompt}")

        # 5. 记忆写入（旁路队列 -> 最终一致，轮询）
        await chat(http, "我家猫叫Lumina，对牛奶过敏")
        exported: dict = {}
        for _ in range(30):
            exported = (await http.get("/agent/memory/me/export", headers=HEADERS)).json()
            if exported.get("facts"):
                break
            await asyncio.sleep(0.2)
        keys = {f["key"]: f for f in exported.get("facts", [])}
        check(results, "记忆可导出", "pet_name" in keys, f"facts={list(keys)}")
        check(
            results,
            "导出带中文标签",
            keys.get("pet_name", {}).get("label") == "宠物名字",
            keys.get("pet_name", {}).get("label", ""),
        )

        # 6. 删除 -> 再导出为空 -> 再删 404
        deleted = await http.delete("/agent/memory/me", params={"key": "allergy"}, headers=HEADERS)
        check(results, "删除记忆", deleted.status_code == 200 and deleted.json().get("deleted") is True, deleted.text)
        after = (await http.get("/agent/memory/me/export", headers=HEADERS)).json()
        check(results, "删除后导出不含该键", "allergy" not in {f["key"] for f in after["facts"]})
        again = await http.delete("/agent/memory/me", params={"key": "allergy"}, headers=HEADERS)
        check(results, "重复删除返回 404", again.status_code == 404, str(again.status_code))

        # 7. 在途巡检：造一条「取走后进程死掉」的审计消息
        client = aioredis.from_url(REDIS_URL, decode_responses=True, protocol=2)
        event_id = f"9{int(time.time() * 1000)}"
        stale = {
            "id": event_id,
            "topic": "agent.audit.tool",
            "key": f"{UID}:sweep",
            "payload": {
                "run_id": "1794000000000000001",
                "name": "get_pet_profile",
                "ok": True,
                "code": None,
                "latency_ms": 5,
                "args_digest": "deadbeefdeadbeef",
            },
            "attempt": 3,
        }
        raw = json.dumps(stale, ensure_ascii=False)
        await client.lpush("pet:task:agent.audit.tool:processing", raw)
        await client.zadd("pet:task:agent.audit.tool:claimed", {raw: time.time() - 60})

        seen = False
        for _ in range(40):
            await asyncio.sleep(0.5)
            with pymysql.connect(**MYSQL) as conn, conn.cursor() as cur:
                cur.execute("SELECT tool_name, ok FROM tool_call_log WHERE id=%s", (int(event_id),))
                row = cur.fetchone()
            if row:
                seen = True
                break
        claimed_left = await client.zcard("pet:task:agent.audit.tool:claimed")
        processing_left = await client.llen("pet:task:agent.audit.tool:processing")
        await client.aclose()
        check(results, "巡检回收并被消费", seen, f"tool_call_log id={event_id}")
        check(
            results,
            "在途/登记清空",
            claimed_left == 0 and processing_left == 0,
            f"claimed={claimed_left} processing={processing_left}",
        )

    passed = sum(1 for r in results if r.ok)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
