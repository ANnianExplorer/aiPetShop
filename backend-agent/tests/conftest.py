"""测试基座：不碰真模型、真 MySQL、真 Java 后端。

约定：
- 模型 = `ScriptedModel`（按脚本出牌）；
- 存储 = `InMemoryRepository`（语义与 MySQL 版一致，用同一套契约测试）；
- Java 后端 = `httpx.MockTransport`，返回与真实 controller 同形的 `{"code":0,"data":...}`。
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from app.api import create_app
from app.config import Settings
from app.llm import ScriptedModel
from app.storage import InMemoryRepository

# 所有用例的文档落盘目录都放在这个根目录下，会话结束一次性删除，
# 否则每跑一次测试就在 cwd 里留下几百个空目录
_DOCS_ROOT = tempfile.mkdtemp(prefix="pet-docs-")


@pytest.fixture(scope="session", autouse=True)
def _cleanup_docs_root() -> Any:
    yield
    shutil.rmtree(_DOCS_ROOT, ignore_errors=True)


JAVA_PET = {"id": "5001", "name": "Lumina", "breed": "布偶", "age": 2}
JAVA_LOG_PAGE = {
    "records": [
        {
            "id": "7001",
            "title": "疫苗记录",
            "type": "vaccine",
            "content": "2026-09-01 猫三联加强针",
            "createTime": "2026-09-01 10:00:00",
        }
    ],
    "total": 1,
}

_JAVA_ROUTES = {
    "/api/v1/auth/current": {"id": "1001", "role": "user", "nickname": "小年"},
    "/api/v1/pet/list": [JAVA_PET],
    "/api/v1/pet/get/vo": JAVA_PET,
    "/api/v1/health/dashboard": {"petId": "5001", "heartRate": 92, "sleepHours": 9.5},
    "/api/v1/health/record/weekly": [{"date": "2026-11-05", "steps": 3200}],
    "/api/v1/log/list/page/vo": JAVA_LOG_PAGE,
}


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "env": "test",
        "llm_api_key": "test-key",
        "llm_model": "scripted",
        "auth_mode": "header",
        "repo_backend": "memory",
        # 每个 Settings 一份独立临时目录，测试之间不串文件；
        # 统一挂到会话级根目录下，跑完由 _cleanup_docs_root 一次性删除
        "doc_storage_dir": tempfile.mkdtemp(prefix="case-", dir=_DOCS_ROOT),
    }
    base.update(overrides)
    return Settings(**base)


def java_handler(request: httpx.Request) -> httpx.Response:
    data = _JAVA_ROUTES.get(request.url.path)
    if data is None:
        return httpx.Response(404, json={"code": 40400, "message": f"unknown {request.url.path}"})
    return httpx.Response(200, json={"code": 0, "data": data, "message": "ok"})


def make_http() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(java_handler))


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def repo() -> InMemoryRepository:
    return InMemoryRepository()


@pytest.fixture
async def client(
    settings: Settings, repo: InMemoryRepository
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(
        settings, model=ScriptedModel(), repo=repo, http_client=make_http()
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://agent"
    ) as http:
        http.app = app  # type: ignore[attr-defined]
        yield http


AUTH_HEADERS = {"satoken": "token-1001", "x-user-id": "1001"}


def parse_sse(body: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for block in body.strip().split("\n\n"):
        if not block.strip():
            continue
        event: dict[str, Any] = {"id": 0, "event": "", "data": {}}
        for line in block.splitlines():
            if line.startswith("id: "):
                event["id"] = int(line[4:])
            elif line.startswith("event: "):
                event["event"] = line[7:]
            elif line.startswith("data: "):
                event["data"] = json.loads(line[6:])
        events.append(event)
    return events
