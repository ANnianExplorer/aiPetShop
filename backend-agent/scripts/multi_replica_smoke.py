"""B2 多副本验证：两个 Agent 实例共享 MySQL/Redis 时的四项一致性。

前置：
  - 两份 uvicorn 用同一套 `REPO_BACKEND=mysql`、`EVENT_BACKEND=redis`、
    `RATE_LIMIT_BACKEND=redis`、`TASK_BACKEND=redis`、`AUTH_MODE=backend`；
  - Java 后端（8080）可登录，Redis 可连。

检查项：
  1) 两个副本 `/healthz`、`/readyz` 都 ready；
  2) 在 A 发起的 run，能在 B 上回放事件（事件总线的 Redis 共享）；
  3) 同一 `client_message_id` 分别打到 A、B，命中同一个 run（幂等跨副本）；
  4) 只投一条任务消息，A+B 的 `processed` 之和为 1（不重复消费）；
  5) B 能读到 A 写入的长期记忆（MySQL 共享）；
  6) 限流共享：A 打满窗口后 B 立刻 429；
  7) 两个副本看到的队列现场一致。

用法：
  python -m scripts.multi_replica_smoke
环境变量（有默认值）：
  SMOKE_AGENT_A/B、SMOKE_JAVA_BASE、SMOKE_REDIS_URL、SMOKE_DB_DSN
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field

import httpx
import redis.asyncio as redis

from app.tasks.base import TaskMessage

AGENT_A = os.environ.get("SMOKE_AGENT_A", "http://127.0.0.1:8099")
AGENT_B = os.environ.get("SMOKE_AGENT_B", "http://127.0.0.1:8100")
JAVA_BASE = os.environ.get("SMOKE_JAVA_BASE", "http://127.0.0.1:8080/api/v1")
REDIS_URL = os.environ.get("SMOKE_REDIS_URL", "redis://127.0.0.1:6379/0")

ADMIN = ("13800000001", "123456")  # 管理员，看全局
USER = ("13800000002", "123456")  # 普通用户，验隔离与限流
LIMITER = ("13800000003", "123456")  # 专用于限流，避免污染其他用例


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class Checker:
    results: list[Result] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append(Result(name, ok, detail))
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}: {detail}")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.ok)


async def login(client: httpx.AsyncClient, phone: str, password: str) -> str:
    resp = await client.post(f"{JAVA_BASE}/auth/login", json={"phone": phone, "password": password})
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 0:
        raise RuntimeError(f"登录失败 {phone}: {body}")
    return body["data"]["token"]


def parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    current: dict[str, object] = {}
    for line in body.splitlines():
        if not line.strip():
            if "event" in current:
                events.append(current)
            current = {}
            continue
        if line.startswith("id:"):
            current["id"] = line[3:].strip()
        elif line.startswith("event:"):
            current["event"] = line[6:].strip()
        elif line.startswith("data:"):
            raw = line[5:].strip()
            try:
                current["data"] = json.loads(raw)
            except json.JSONDecodeError:
                current["data"] = raw
    if "event" in current:
        events.append(current)
    return events


async def chat(
    client: httpx.AsyncClient,
    base: str,
    token: str,
    text: str,
    *,
    client_message_id: str | None = None,
) -> tuple[int, list[dict]]:
    payload: dict[str, object] = {"message": text, "channel": "app"}
    if client_message_id:
        payload["client_message_id"] = client_message_id
    resp = await client.post(
        f"{base}/agent/chat",
        json=payload,
        headers={"satoken": token},
        timeout=30.0,
    )
    return resp.status_code, parse_sse(resp.text) if resp.status_code == 200 else []


async def main() -> int:
    checks = Checker()
    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1) 两个副本都活着
        for name, base in (("A", AGENT_A), ("B", AGENT_B)):
            health = await client.get(f"{base}/healthz")
            ready = await client.get(f"{base}/readyz")
            checks.add(
                f"replica {name} ready",
                health.status_code == 200 and ready.status_code == 200,
                f"healthz={health.status_code} readyz={ready.status_code}",
            )

        admin = await login(client, *ADMIN)
        user = await login(client, *USER)
        limiter = await login(client, *LIMITER)

        # 2) 跨副本事件回放
        status, events = await chat(client, AGENT_A, user, "你好呀")
        route = next((e for e in events if e["event"] == "route"), None)
        run_id = (route or {}).get("data", {}).get("run_id")
        replay = (
            await client.get(f"{AGENT_B}/agent/runs/{run_id}/events", headers={"satoken": user})
            if run_id
            else None
        )
        replay_events = parse_sse(replay.text) if replay is not None and replay.status_code == 200 else []
        checks.add(
            "events visible across replicas",
            bool(run_id) and any(e["event"] == "done" for e in replay_events),
            f"run={run_id} b_events={len(replay_events)}",
        )

        # 3) 幂等跨副本：同一个 client_message_id 打到两个副本
        key = f"mr-{uuid.uuid4().hex[:12]}"
        _, first = await chat(client, AGENT_A, user, "继续聊一句", client_message_id=key)
        _, second = await chat(client, AGENT_B, user, "继续聊一句", client_message_id=key)
        first_run = next((e["data"]["run_id"] for e in first if e["event"] == "route"), None)
        second_run = next((e["data"]["run_id"] for e in second if e["event"] == "route"), None)
        second_done = next((e["data"] for e in second if e["event"] == "done"), {})
        checks.add(
            "idempotency across replicas",
            first_run is not None and first_run == second_run and second_done.get("replayed") is True,
            f"a={first_run} b={second_run} replayed={second_done.get('replayed')}",
        )

        # 4) 单条任务只被一个副本消费
        before_a = await client.get(f"{AGENT_A}/agent/admin/tasks", headers={"satoken": admin})
        before_b = await client.get(f"{AGENT_B}/agent/admin/tasks", headers={"satoken": admin})
        base_processed = before_a.json()["processed"] + before_b.json()["processed"]

        rds = redis.from_url(REDIS_URL, decode_responses=True, protocol=2)
        try:
            task = TaskMessage(
                id=f"9{int(time.time() * 1000)}",
                topic="agent.audit.tool",
                key="multi-replica",
                payload={
                    "run_id": f"1{int(time.time() * 1000)}",
                    "name": "get_pet_profile",
                    "ok": True,
                    "code": None,
                    "latency_ms": 3,
                    "args_digest": "0123456789abcdef",
                },
            )
            await rds.lpush(f"pet:task:{task.topic}", json.dumps(task.to_json(), ensure_ascii=False))

            deadline = time.time() + 10
            observed = 0
            while time.time() < deadline:
                a = await client.get(f"{AGENT_A}/agent/admin/tasks", headers={"satoken": admin})
                b = await client.get(f"{AGENT_B}/agent/admin/tasks", headers={"satoken": admin})
                observed = a.json()["processed"] + b.json()["processed"] - base_processed
                if observed >= 1:
                    break
                await asyncio.sleep(0.3)
            checks.add(
                "single delivery across replicas",
                observed == 1,
                f"processed_delta={observed}",
            )

            # 7) 队列现场一致
            a_stats = a.json()["topics"]
            b_stats = b.json()["topics"]
            checks.add(
                "queue view consistent",
                {t["topic"] for t in a_stats} == {t["topic"] for t in b_stats},
                f"a={[t['topic'] for t in a_stats]}",
            )
        finally:
            await rds.aclose()

        # 5) 记忆跨副本可见
        await chat(client, AGENT_A, user, "我家猫叫团子，对鸡肉过敏")
        await asyncio.sleep(1.5)  # 记忆走旁路队列，给它一点时间
        memory = await client.get(f"{AGENT_B}/agent/memory/me", headers={"satoken": user})
        facts = memory.json().get("facts", []) if memory.status_code == 200 else []
        keys = {f["key"] for f in facts}
        checks.add(
            "memory visible across replicas",
            {"pet_name", "allergy"} <= keys,
            f"keys={sorted(keys)}",
        )

        # 6) 限流共享
        codes = []
        for index in range(21):
            base = AGENT_A if index % 2 == 0 else AGENT_B
            status, _ = await chat(client, base, limiter, "限流测试")
            codes.append(status)
        last_status, _ = await chat(client, AGENT_B, limiter, "限流测试")
        checks.add(
            "rate limit shared",
            429 in codes and last_status == 429,
            f"first_429_at={codes.index(429) if 429 in codes else None} b_status={last_status}",
        )

    total = len(checks.results)
    passed = total - checks.failed
    print(json.dumps({"passed": passed, "total": total}, ensure_ascii=False))
    return 0 if checks.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
