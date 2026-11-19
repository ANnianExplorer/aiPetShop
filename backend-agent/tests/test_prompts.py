"""提示词版本化（BACKLOG D6）：改正文必须升版本，一轮 run 必须能对上是哪一版。

三条不变量：
1. 每个登记版本的正文 sha256 == 冻结哈希（原地改字 → 红）；
2. 当前版本 = 登记表最后一条，版本号形如 `YYYY-MM-DD.n`；
3. 一轮对话把版本号写进 assistant 消息 meta 和 `run finished` 日志——
   否则线上排查「回答风格为什么变了」无从对账。
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
import pytest
from conftest import AUTH_HEADERS, parse_sse

from app.domain.models import Role
from app.graph.prompts import (
    FROZEN_SHA256,
    PROMPT_SHA256,
    PROMPT_VERSION,
    PROMPT_VERSIONS,
    SYSTEM_PROMPT,
    latest_version,
    sha256_of,
)
from app.storage import InMemoryRepository

VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.\d+$")


def test_every_version_hash_is_frozen() -> None:
    for version, text in PROMPT_VERSIONS.items():
        assert version in FROZEN_SHA256, f"{version} 没有冻结哈希"
        assert sha256_of(text) == FROZEN_SHA256[version], (
            f"{version} 的正文被原地改了：请新增版本号（YYYY-MM-DD.n）并补冻结哈希，"
            "不要改历史版本"
        )


def test_current_version_is_last_and_well_formed() -> None:
    assert latest_version() == PROMPT_VERSION
    assert next(reversed(PROMPT_VERSIONS)) == PROMPT_VERSION
    assert VERSION_RE.match(PROMPT_VERSION), PROMPT_VERSION
    assert all(VERSION_RE.match(version) for version in PROMPT_VERSIONS)
    assert PROMPT_SHA256 == sha256_of(SYSTEM_PROMPT) == FROZEN_SHA256[PROMPT_VERSION]
    assert len(PROMPT_SHA256) == 64


@pytest.mark.parametrize("phrase", ["不替代兽医诊断", "必须先调用工具", "不知道就说不知道"])
def test_safety_rules_survive_edits(phrase: str) -> None:
    """安全规则是产品底线，措辞可以改，但删掉必须让 CI 红一次。"""
    assert phrase in SYSTEM_PROMPT


def test_pet_list_rule_is_present() -> None:
    """宠物列表问题必须显式引导到 get_pet_profile，避免模型声称「没有工具」。"""
    assert "get_pet_profile" in SYSTEM_PROMPT
    assert "没有宠物查询工具" in SYSTEM_PROMPT


async def _chat(client: httpx.AsyncClient, text: str = "你好呀") -> str:
    resp = await client.post(
        "/agent/chat", json={"message": text, "channel": "app"}, headers=AUTH_HEADERS
    )
    assert resp.status_code == 200
    events = parse_sse(resp.text)
    route = next(event for event in events if event["event"] == "route")
    return route["data"]["session_id"]


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.asyncio
async def test_run_meta_records_prompt_version(
    client: httpx.AsyncClient, repo: InMemoryRepository
) -> None:
    session_id = await _chat(client)
    messages = await repo.list_messages(session_id, limit=10)
    assistant = [m for m in messages if m.role is Role.ASSISTANT]
    assert assistant, "一轮对话应当落一条 assistant 消息"
    meta: dict[str, Any] = assistant[-1].meta
    assert meta["prompt_version"] == PROMPT_VERSION
    # 版本号旁边还有模型名：定位「答案变了」时两个维度一起看
    assert meta["model"]


@pytest.mark.asyncio
async def test_run_finished_log_carries_prompt_version(client: httpx.AsyncClient) -> None:
    handler = _Capture()
    logger = logging.getLogger("agent.run")
    logger.addHandler(handler)
    try:
        await _chat(client)
    finally:
        logger.removeHandler(handler)

    finished = [r for r in handler.records if r.getMessage() == "run finished"]
    assert finished, "应当打一条 run finished 日志"
    ctx: dict[str, Any] = getattr(finished[-1], "ctx", {})
    assert ctx["prompt_version"] == PROMPT_VERSION
    assert "你好呀" not in str(ctx), "ADR-0007：日志不落消息正文"
