"""本地 Java 后端桩：只为端到端验证，不参与生产。

模仿真实 `/api/v1` 的契约：`{code, data, message}`，`data` 里 Long 一律字符串
（对齐 `backend/.../config/JsonConfig.java` 的 `Long → String`）。

    python -m uvicorn tests.stub_java:app --port 8097
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request

app = FastAPI()

PET = {
    "id": "5001",
    "name": "Lumina",
    "species": "cat",
    "breed": "英短",
    "birthday": "2023-04-01",
    "weight": 4.6,
}
LOG = {
    "id": "7001",
    "title": "疫苗记录",
    "type": "vaccine",
    "content": "猫三联，第二针",
    "createTime": "2026-09-01 10:20:00",
}


def ok(data: Any) -> dict[str, Any]:
    return {"code": 0, "data": data, "message": "ok"}


def fail(code: int, message: str) -> dict[str, Any]:
    return {"code": code, "data": None, "message": message}


@app.get("/api/v1/auth/current")
async def current(request: Request):
    token = request.headers.get("satoken") or ""
    if not token:
        return fail(40100, "未登录")
    # token-<uid> 约定：让端到端测试能造出"另一个用户"
    suffix = token.rsplit("-", 1)[-1]
    user_id = suffix if suffix.isdigit() else "1001"
    return ok({"id": user_id, "role": "user", "nickname": "测试用户"})


@app.get("/api/v1/pet/list")
async def pet_list():
    return ok([PET])


@app.get("/api/v1/pet/get/vo")
async def pet_get(id: str | None = None):
    if id and id != PET["id"]:
        return fail(40400, "宠物不存在")
    return ok(PET)


@app.get("/api/v1/health/dashboard")
async def dashboard(petId: str | None = None):
    return ok({"petId": petId or PET["id"], "heartRate": 92, "sleepHours": 7.5})


@app.get("/api/v1/health/record/weekly")
async def weekly(petId: str | None = None):
    return ok([{"date": "2026-11-05", "heartRate": 90, "steps": 4200}])


@app.post("/api/v1/log/list/page/vo")
async def log_page(request: Request):
    body = await request.json()
    keyword = (body.get("searchText") or "").strip()
    records = [LOG] if keyword in ("", "疫苗", "记录") else []
    return ok({"records": records, "total": len(records), "current": 1, "pageSize": 5})
