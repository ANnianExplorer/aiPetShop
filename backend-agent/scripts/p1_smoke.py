"""P1 真进程验收：配额 429 / 用量聚合 / 记忆写入与召回。

前置：8097 stub_java、8098 stub_llm、8099 agent 三个进程已启动。

跑：
    .venv\\Scripts\\python -m scripts.p1_smoke

设计说明：
- 用独立账号（token-7007）验收，不污染 e2e_smoke 的 token-1001；
- 限流放最后：一旦触发 429，该账号在窗口内就不能再对话；
- 记忆验收走 `GET /agent/memory/me`，而不是猜模型输出——断言的是存储里真有什么。
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

import httpx

BASE = "http://127.0.0.1:8099"
TOKEN = "token-7007"
HEADERS = {"satoken": TOKEN}


@dataclass
class Result:
    name: str
    ok: bool
    note: str = ""


def events(response: httpx.Response) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in response.text.splitlines():
        if line.startswith("event:"):
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
    return client.post("/agent/chat", json=payload, headers=HEADERS, timeout=30)


def done_of(response: httpx.Response) -> dict[str, Any]:
    rows = events(response)
    return next((row["data"] for row in rows if row["event"] == "done"), {})


def main() -> int:
    results: list[Result] = []
    with httpx.Client(base_url=BASE, timeout=30) as client:
        # ---- 1. 初始状态：这个账号还没被记住任何东西
        before = client.get("/agent/memory/me", headers=HEADERS).json()
        results.append(Result("记忆初始为空", before["facts"] == [], json.dumps(before, ensure_ascii=False)[:120]))

        # ---- 2. 说一句带事实的话，触发写入
        learned = chat(client, "我家猫叫Lumina，对牛奶过敏")
        results.append(Result("写入轮成功", learned.status_code == 200, str(learned.status_code)))

        after = client.get("/agent/memory/me", headers=HEADERS).json()
        facts = {f["key"]: f for f in after["facts"]}
        results.append(
            Result(
                "记忆已落库",
                facts.get("allergy", {}).get("value") == "牛奶" and facts.get("pet_name", {}).get("value") == "Lumina",
                json.dumps(after["facts"], ensure_ascii=False)[:200],
            )
        )
        results.append(
            Result(
                "记忆带标签与置信度",
                facts.get("allergy", {}).get("label") == "过敏" and facts["allergy"]["confidence"] >= 0.9,
                f"label={facts.get('allergy', {}).get('label')} conf={facts.get('allergy', {}).get('confidence')}",
            )
        )

        # ---- 3. 第二轮：记忆在服务端参与上下文（这里只验流程不被记忆拖垮）
        second = chat(client, "它对什么过敏")
        body = done_of(second)
        results.append(
            Result("召回轮成功", second.status_code == 200 and bool(body.get("answer")), str(body.get("answer"))[:60])
        )

        # ---- 4. 重复同一句话不该产生第二条事实
        chat(client, "我家猫叫Lumina，对牛奶过敏")
        again = client.get("/agent/memory/me", headers=HEADERS).json()
        results.append(
            Result("重复不产生重复事实", len(again["facts"]) == 2, f'{len(again["facts"])} 条')
        )

        # ---- 5. 用量聚合
        usage = client.get("/agent/usage/me?days=7", headers=HEADERS).json()
        results.append(
            Result(
                "用量按账号聚合",
                usage["runs"] == 3 and usage["total_tokens"] > 0,
                json.dumps(usage, ensure_ascii=False),
            )
        )

        # ---- 6. 限流：默认 20 次/分钟，打满后必须 429 + Retry-After
        codes: list[int] = []
        limited: httpx.Response | None = None
        for _ in range(25):
            response = chat(client, "hi")
            codes.append(response.status_code)
            if response.status_code == 429:
                limited = response
                break

        results.append(
            Result("超配额返回 429", limited is not None, f"codes={codes[-3:]}"),
        )
        if limited is not None:
            payload = limited.json()
            results.append(
                Result(
                    "429 带 Retry-After 与 code",
                    payload.get("code") == "rate_limited" and int(limited.headers.get("Retry-After", "0")) >= 1,
                    f'code={payload.get("code")} retry={limited.headers.get("Retry-After")}',
                )
            )

    width = max(len(r.name) for r in results)
    for r in results:
        print(f"[{'PASS' if r.ok else 'FAIL'}] {r.name.ljust(width)}  {r.note}")
    failed = [r for r in results if not r.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
