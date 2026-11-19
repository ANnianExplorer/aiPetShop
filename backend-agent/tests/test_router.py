"""意图路由：关键词表的回归测试。表被改坏，这里先红。"""

from __future__ import annotations

import pytest

from app.domain.models import Intent, Route
from app.domain.router import classify


@pytest.mark.parametrize(
    ("question", "intent", "route", "reason"),
    [
        ("你好呀", Intent.CHAT, Route.L1, "greeting"),
        ("在吗", Intent.CHAT, Route.L1, "greeting"),
        ("", Intent.CHAT, Route.L1, "empty"),
        ("给我讲个笑话", Intent.CHAT, Route.L1, "default"),
        ("我家猫最近呕吐", Intent.LOG, Route.L2, "keyword:呕吐"),
        ("上次疫苗是什么时候", Intent.LOG, Route.L2, "keyword:上次"),
        ("最近心率怎么样", Intent.HEALTH, Route.L2, "keyword:心率"),
        ("它的品种是什么", Intent.PROFILE, Route.L2, "keyword:品种"),
        ("我现在有什么宠物", Intent.PROFILE, Route.L2, "keyword:宠物"),
        ("我的宠物叫什么", Intent.PROFILE, Route.L2, "keyword:宠物"),
    ],
)
def test_classify(question: str, intent: Intent, route: Route, reason: str) -> None:
    decision = classify(question)
    assert (decision.intent, decision.route, decision.reason) == (intent, route, reason)


def test_greeting_only_short_text() -> None:
    # 长句里的"你好"不算纯寒暄：用户后面往往跟着真需求
    long_text = "你好，我想问一下我家猫最近的健康数据趋势"
    assert classify(long_text).route is Route.L2


def test_health_beats_log() -> None:
    # 同一句里既有"记录"又有"心率"，按优先级归健康
    decision = classify("看看这只宠物最近的健康记录")
    assert decision.intent is Intent.HEALTH
