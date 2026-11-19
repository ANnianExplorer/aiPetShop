"""C1 第一刀：情景记忆的抽取、幂等、召回与隔离。

这里只测规则与服务层；HTTP 形状在 `test_memory_api.py`，跨轮注入在 `test_api.py`。
"""

from __future__ import annotations

from datetime import datetime

from app.domain.models import MemoryEpisode
from app.memory.episodes import (
    EPISODE_KINDS,
    extract_episode,
    format_episode_line,
    label_of_kind,
    score_episode,
    select_episodes,
)
from app.memory.service import MemoryService
from app.storage.memory import InMemoryRepository

NOW = datetime(2026, 11, 19, 21, 0, 0)


def test_extracts_bath_with_relative_date() -> None:
    candidate = extract_episode("上周给豆豆洗澡了", now=NOW)
    assert candidate is not None
    assert candidate.kind == "bath"
    assert candidate.label == "洗澡"
    assert candidate.occurred_at == "2026-11-12 00:00:00"
    assert candidate.summary == "上周给豆豆洗澡了"
    assert candidate.time_word == "上周"


def test_extracts_event_without_time_word_when_completed() -> None:
    candidate = extract_episode("刚给豆豆洗了澡", now=NOW)
    assert candidate is not None
    assert candidate.kind == "bath"
    assert candidate.occurred_at == "2026-11-19 00:00:00"


def test_extracts_numeric_days_ago() -> None:
    candidate = extract_episode("豆豆 3 天前吐了", now=NOW)
    assert candidate is not None
    assert candidate.kind == "vomit"
    assert candidate.occurred_at == "2026-11-16 00:00:00"


def test_extracts_last_month() -> None:
    candidate = extract_episode("上个月给它做了驱虫", now=NOW)
    assert candidate is not None
    assert candidate.kind == "deworm"
    assert candidate.occurred_at == "2026-10-20 00:00:00"


def test_question_is_not_an_episode() -> None:
    assert extract_episode("上次洗澡是什么时候？", now=NOW) is None


def test_negation_is_not_an_episode() -> None:
    assert extract_episode("今天没洗澡", now=NOW) is None


def test_habit_is_not_an_episode() -> None:
    assert extract_episode("它洗澡特别乖", now=NOW) is None


def test_unknown_event_is_not_an_episode() -> None:
    assert extract_episode("昨天带它去公园了", now=NOW) is None


def test_label_of_kind_falls_back_to_raw_kind() -> None:
    assert label_of_kind("bath") == "洗澡"
    assert label_of_kind("unknown") == "unknown"
    assert "bath" in EPISODE_KINDS


async def test_record_episode_is_idempotent_by_source_message() -> None:
    repo = InMemoryRepository()
    service = MemoryService(repo)

    first = await service.record_episode(
        "1001", None, "昨天给豆豆洗澡了", session_id="11", message_id="9001", now=NOW
    )
    second = await service.record_episode(
        "1001", None, "昨天给豆豆洗澡了", session_id="11", message_id="9001", now=NOW
    )

    assert first is not None and second is not None
    assert first.id == second.id
    episodes = await repo.list_memory_episodes("1001", None, 10)
    assert len(episodes) == 1
    assert episodes[0].source_message_id == "9001"
    assert episodes[0].session_id == "11"


async def test_record_episode_skips_question() -> None:
    repo = InMemoryRepository()
    service = MemoryService(repo)
    saved = await service.record_episode("1001", None, "上次洗澡是什么时候", now=NOW)
    assert saved is None
    assert await repo.list_memory_episodes("1001", None, 10) == []


async def test_episode_lines_recall_matching_event_only() -> None:
    repo = InMemoryRepository()
    service = MemoryService(repo)
    bath = await service.record_episode(
        "1001", None, "上周给豆豆洗澡了", message_id="9001", now=NOW
    )
    await service.record_episode(
        "1001", None, "昨天带它去打了疫苗", message_id="9002", now=NOW
    )
    assert bath is not None

    lines = await service.episode_lines("1001", None, "上次洗澡是什么时候", now=NOW)
    assert lines == ["- 2026-11-12（洗澡）：上周给豆豆洗澡了（来源消息 9001）"]
    unrelated = await service.episode_lines("1001", None, "它今天吃饭怎么样", now=NOW)
    assert unrelated == []


async def test_episode_is_isolated_by_user_and_pet() -> None:
    repo = InMemoryRepository()
    service = MemoryService(repo)
    await service.record_episode(
        "1001", "p1", "昨天给豆豆洗澡了", message_id="9001", now=NOW
    )

    assert await service.episode_lines("1001", "p1", "上次洗澡是什么时候", now=NOW)
    assert await service.episode_lines("1001", "p2", "上次洗澡是什么时候", now=NOW) == []
    assert await service.episode_lines("2002", "p1", "上次洗澡是什么时候", now=NOW) == []


def test_format_episode_line_without_source() -> None:
    episode = MemoryEpisode(
        id="1",
        user_id="1001",
        summary="豆豆吐了",
        occurred_at="2026-11-18 00:00:00",
        kind="vomit",
    )
    assert format_episode_line(episode) == "- 2026-11-18（呕吐）：豆豆吐了"


def test_select_episodes_requires_kind_match() -> None:
    old = MemoryEpisode(
        id="1",
        user_id="1001",
        summary="上周给豆豆洗澡了",
        occurred_at="2026-11-12 00:00:00",
        kind="bath",
    )
    unrelated = MemoryEpisode(
        id="2",
        user_id="1001",
        summary="昨天带它去打了疫苗",
        occurred_at="2026-11-18 00:00:00",
        kind="vaccine",
    )
    picked = select_episodes("上次洗澡是什么时候", [old, unrelated], now=NOW)
    assert [episode.id for episode in picked] == ["1"]
    assert score_episode("上次洗澡是什么时候", old, now=NOW) >= 0.5
