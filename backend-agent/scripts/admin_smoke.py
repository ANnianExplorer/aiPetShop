"""管理端只读接口的真进程冒烟（跑在 uvicorn 上，不用 TestClient）。

覆盖四条最容易回归的路径：
1. 普通用户访问管理端 → 403（不是 404，缺权限就是缺权限）；
2. 管理员列表能看到刚产生的会话；
3. 详情里能看到消息与运行步骤（step），说明轨迹真的落库了；
4. 全局用量与按天趋势能算出来。

用法：先起 stub_java(8097) / stub_llm(8098) / uvicorn(8099) 后
`python -m scripts.admin_smoke`
"""

from __future__ import annotations

import contextlib
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE = "http://127.0.0.1:8099"
USER_TOKEN = "token-1001"
ADMIN_TOKEN = "token-admin"


@dataclass
class Result:
    name: str
    ok: bool
    detail: str


def call(
    path: str, *, method: str = "GET", token: str, body: dict | None = None
) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "satoken": token,
            "content-type": "application/json",
            "accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}


def chat(token: str, message: str, session_id: str | None = None) -> tuple[int, str]:
    """发一条 L1 消息，把 SSE 读完，返回 (状态码, 会话ID)。"""
    payload: dict = {"message": message, "channel": "app"}
    if session_id:
        payload["session_id"] = session_id
    req = urllib.request.Request(
        BASE + "/agent/chat",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"satoken": token, "content-type": "application/json"},
    )
    sid = session_id or ""
    with urllib.request.urlopen(req, timeout=30) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if line.startswith("data:") and '"session_id"' in line:
                with contextlib.suppress(json.JSONDecodeError):
                    sid = json.loads(line[5:].strip()).get("session_id") or sid
        return resp.status, sid


def main() -> int:
    results: list[Result] = []

    status, body = call("/agent/admin/sessions", token=USER_TOKEN)
    results.append(
        Result("普通用户被拒绝", status == 403 and body.get("code") == "forbidden", f"{status} {body}")
    )

    status, sid = chat(USER_TOKEN, "你好呀")
    results.append(Result("造一条会话", status == 200 and bool(sid), f"{status} session={sid}"))

    status, body = call("/agent/admin/sessions?user_id=1001", token=ADMIN_TOKEN)
    items = body.get("items") or []
    results.append(
        Result(
            "管理员看到会话",
            status == 200 and any(i["id"] == sid for i in items),
            f"{status} total={body.get('total')} first={items[0] if items else None}",
        )
    )

    status, body = call(f"/agent/admin/sessions/{sid}", token=ADMIN_TOKEN)
    msgs = body.get("messages") or []
    runs = body.get("runs") or []
    steps = [s for r in runs for s in r.get("steps") or []]
    results.append(
        Result(
            "详情含消息与轨迹",
            status == 200 and len(msgs) >= 2 and bool(steps),
            f"{status} messages={len(msgs)} runs={len(runs)} steps={len(steps)} "
            f"kinds={[s['kind'] for s in steps]}",
        )
    )

    status, body = call("/agent/admin/usage?days=7", token=ADMIN_TOKEN)
    results.append(
        Result(
            "全局用量与趋势",
            status == 200 and body.get("runs", 0) >= 1 and isinstance(body.get("by_day"), list),
            f"{status} {body}",
        )
    )

    status, body = call("/agent/admin/sessions", token="")
    results.append(Result("无 token 401", status == 401, f"{status} {body.get('code')}"))

    failed = [r for r in results if not r.ok]
    for r in results:
        print(f"[{'PASS' if r.ok else 'FAIL'}] {r.name}: {r.detail}")
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
