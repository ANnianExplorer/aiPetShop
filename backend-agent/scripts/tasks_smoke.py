"""S1.9 真进程验收：旁路队列的现场、死信重放、启动补偿。

前置：8097 stub_java、8098 stub_llm、8099 agent（`TASK_BACKEND=redis`）三个进程已启动。

跑：
    .venv\\Scripts\\python -m scripts.tasks_smoke

为什么这么写：
- 死信不是"后台自己会好"的东西，必须能被看见（`GET /agent/admin/tasks`）并手动放回
  （`POST /agent/admin/tasks/dead-letters/replay`），所以冒烟直接构造一条死信；
- 构造方式是把消息**直接塞进死信列表**（而不是等消费失败三次），避免依赖真实下游故障；
  消息体本身是合法的，重放后应被正常消费——这样才证明"重放 → 消费 → 落库"整条链路通；
- 真机是 Redis 队列，用 `redis.asyncio` 直连（与生产同一条路径），不走 HTTP 伪造。
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass

import httpx

BASE = "http://127.0.0.1:8099"
ADMIN = {"satoken": "token-admin"}
USER = {"satoken": "token-1001"}
TOPIC = "agent.audit.tool"
DLQ_KEY = f"pet:task:{TOPIC}:dlq"
REDIS_URL = "redis://127.0.0.1:6379/0"


@dataclass
class Result:
    name: str
    ok: bool
    note: str = ""


async def _inject_dead_letter() -> str:
    """往死信列表里放一条结构合法的审计消息（等价于「修好下游后要重放的那条」）。"""
    from redis.asyncio import from_url

    message_id = f"9{int(time.time() * 1000) % 10**18:018d}"
    message = {
        "id": message_id,
        "topic": TOPIC,
        "key": f"{message_id}:get_pet_profile",
        "payload": {
            "run_id": message_id,
            "name": "get_pet_profile",
            "ok": True,
            "code": None,
            "latency_ms": 12,
            "args_digest": "0123456789abcdef",
        },
        "attempt": 3,
    }
    client = from_url(REDIS_URL, decode_responses=True, protocol=2)
    try:
        await client.lpush(DLQ_KEY, json.dumps(message, ensure_ascii=False))
    finally:
        await client.aclose()
    return message_id


async def main() -> int:
    results: list[Result] = []
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        # ---- 1. 权限：普通用户看不到队列现场
        denied = await client.get("/agent/admin/tasks", headers=USER)
        results.append(Result("普通用户 403", denied.status_code == 403, str(denied.status_code)))

        # ---- 2. 管理员能看到两个 topic，且 queue 已启用
        scene = await client.get("/agent/admin/tasks", headers=ADMIN)
        body = scene.json()
        topics = {t["topic"]: t for t in body.get("topics", [])}
        results.append(
            Result(
                "队列现场可见",
                scene.status_code == 200 and body.get("enabled") is True and TOPIC in topics,
                f'enabled={body.get("enabled")} backend={body.get("backend")} topics={list(topics)}',
            )
        )

        # ---- 3. 构造一条死信，列表里应该多出来
        await _inject_dead_letter()
        after_inject = (await client.get("/agent/admin/tasks", headers=ADMIN)).json()
        dead_after_inject = {t["topic"]: t["dead_letters"] for t in after_inject["topics"]}[TOPIC]
        results.append(
            Result("死信可被观测", dead_after_inject >= 1, f"dead_letters={dead_after_inject}")
        )

        # ---- 4. 非管理员不能重放
        denied_replay = await client.post(
            "/agent/admin/tasks/dead-letters/replay", json={"topic": TOPIC}, headers=USER
        )
        results.append(
            Result("重放需管理员", denied_replay.status_code == 403, str(denied_replay.status_code))
        )

        # ---- 5. 管理员重放，至少把我们塞的那条放回去
        replay = await client.post(
            "/agent/admin/tasks/dead-letters/replay",
            json={"topic": TOPIC, "limit": 20},
            headers=ADMIN,
        )
        replayed = replay.json().get("replayed", 0) if replay.status_code == 200 else -1
        results.append(
            Result("死信重放成功", replay.status_code == 200 and replayed >= 1, f"replayed={replayed}")
        )

        # ---- 6. 重放后由 worker 正常消费：死信清空、队列清空
        async def consumed() -> bool:
            scene = (await client.get("/agent/admin/tasks", headers=ADMIN)).json()
            dead = {t["topic"]: t["dead_letters"] for t in scene["topics"]}[TOPIC]
            depth = {t["topic"]: t["depth"] for t in scene["topics"]}[TOPIC]
            return dead == 0 and depth == 0

        deadline = time.monotonic() + 8.0
        ok = False
        while time.monotonic() < deadline:
            if await consumed():
                ok = True
                break
            await asyncio.sleep(0.2)
        results.append(Result("重放后被消费并清空", ok))

        # ---- 7. 未知 topic 拒绝
        unknown = await client.post(
            "/agent/admin/tasks/dead-letters/replay",
            json={"topic": "agent.nope"},
            headers=ADMIN,
        )
        results.append(
            Result("未知 topic 拒绝", unknown.status_code in (400, 404), str(unknown.status_code))
        )

        # ---- 8. worker 计数在推进（能证明消费真的发生了）
        final = (await client.get("/agent/admin/tasks", headers=ADMIN)).json()
        results.append(
            Result(
                "worker 有消费计数",
                final.get("processed", 0) >= 1,
                f'processed={final.get("processed")} failed={final.get("failed")}',
            )
        )

    width = max(len(r.name) for r in results)
    for r in results:
        print(f"[{'PASS' if r.ok else 'FAIL'}] {r.name.ljust(width)}  {r.note}")
    failed = [r for r in results if not r.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
