"""意图路由：确定性关键词优先，可被单测逐条钉死。

为什么不直接让模型分类：L1 占比 90%，每次省一次模型往返就是省 200ms + 一次计费；
且关键词表坏了能被测试立刻发现，模型分类坏了只能等线上体感。
S2 之后再叠加「小模型兜底 + 置信度阈值」，接口不变。
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Intent, Route

# 顺序即优先级：健康 > 记录 > 档案 > 闲聊。
INTENT_KEYWORDS: tuple[tuple[Intent, tuple[str, ...]], ...] = (
    (
        Intent.HEALTH,
        (
            "健康", "心率", "睡眠", "体重", "步数", "打卡", "数据", "趋势",
            "瘦", "胖", "发烧", "食欲", "体温", "精神",
        ),
    ),
    (
        Intent.LOG,
        (
            "日记", "日志", "记录", "上次", "之前", "有没有过", "照片",
            "疫苗", "驱虫", "洗澡", "呕吐", "拉稀", "用药",
        ),
    ),
    (
        Intent.PROFILE,
        (
            "品种", "多大", "年龄", "绝育", "档案", "几岁", "生日", "性别",
            "宠物", "毛孩子",
        ),
    ),
)

# 纯寒暄：即使命中关键词也不必查数据（"你好呀" 不该触发工具）。
GREETING_PREFIXES = ("你好", "您好", "hi", "hello", "在吗", "嗨", "早上好", "晚上好")


@dataclass(frozen=True)
class RoutingDecision:
    intent: Intent
    route: Route
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"intent": self.intent.value, "route": self.route.value, "reason": self.reason}


def classify(question: str) -> RoutingDecision:
    text = (question or "").strip()
    lowered = text.lower()
    if not text:
        return RoutingDecision(Intent.CHAT, Route.L1, "empty")
    if len(text) <= 12 and lowered.startswith(GREETING_PREFIXES):
        return RoutingDecision(Intent.CHAT, Route.L1, "greeting")

    for intent, words in INTENT_KEYWORDS:
        hit = next((w for w in words if w in text), None)
        if hit is not None:
            return RoutingDecision(intent, Route.L2, f"keyword:{hit}")
    return RoutingDecision(Intent.CHAT, Route.L1, "default")
