"""记忆抽取：规则优先，模型只在「结构化不了的闲聊」里才兜底（S2 才开）。

为什么不用 LLM 抽取：宠物档案里的关键事实（名字、过敏、忌口、体重、年龄）都是
模式极其固定的短句，正则的准确率和成本都碾压一次模型调用；而 LLM 抽取的错误会以
「自信的假事实」形式长期污染记忆，比漏抽危险得多。

每条规则只输出「这一个 span 就是事实值」，不做推理（推理交给业务层）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# key 一旦上线就不能改名：它同时是 memory_fact 的索引与召回时的展示标签
FACT_LABELS: dict[str, str] = {
    "pet_name": "宠物名字",
    "pet_age": "年龄",
    "pet_weight": "体重",
    "allergy": "过敏",
    "food_avoid": "忌口",
    "food_like": "爱吃",
    "vaccine": "疫苗",
}
AGE_UNIT = r"(?:岁|个月)"
WEIGHT_UNIT = r"(?:kg|KG|公斤|千克|斤)"

_RULES: list[tuple[str, re.Pattern[str], float]] = [
    # 「我家猫叫 Lumina」「名字叫咪咪」
    ("pet_name", re.compile(r"(?:名字叫|叫|名叫)\s*(?P<v>[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z·]{0,11})"), 0.85),
    ("pet_age", re.compile(rf"(?P<v>\d{{1,2}})\s*{AGE_UNIT}"), 0.9),
    # 「三岁」「两岁半」：中文数字在口语里比阿拉伯数字更常见
    ("pet_age", re.compile(rf"(?P<v>[一二两三四五六七八九十]{{1,2}})\s*{AGE_UNIT}"), 0.85),
    ("pet_weight", re.compile(rf"(?P<v>\d{{1,2}}(?:\.\d)?)\s*{WEIGHT_UNIT}"), 0.9),
    ("allergy", re.compile(r"对(?P<v>[\u4e00-\u9fa5]{1,8})过敏"), 0.95),
    ("food_avoid", re.compile(r"(?:不吃|不能吃|忌口|别喂)(?P<v>[\u4e00-\u9fa5]{1,8})"), 0.9),
    ("food_like", re.compile(r"(?:爱吃|喜欢|最爱)(?P<v>[\u4e00-\u9fa5]{1,8})"), 0.75),
    ("vaccine", re.compile(r"(?:打了|接种了|打过)(?P<v>[\u4e00-\u9fa5A-Za-z0-9·\- ]{2,20})(?:疫苗|针)"), 0.85),
]

# 句尾语气词不属于事实值：「改名叫小月亮了」不能把「了」存进名字
_TRAILING = "了的呀哦呢吧啊哈嘛"

_CN_DIGITS = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

# 「不吃东西」「喜欢吗」这类不是事实，直接丢弃
_STOPWORDS = {
    "东西",
    "什么",
    "这个",
    "那个",
    "吗",
    "呢",
    "吃",
    "玩",
    "睡",
    "它",
    "他",
    "她",
    "我家",
    "我的",
}


@dataclass(frozen=True)
class MemoryCandidate:
    key: str
    value: str
    confidence: float
    quote: str


def extract(text: str) -> list[MemoryCandidate]:
    """从一句话里抽候选事实：同一 key 只保留第一个命中，避免一句里重复规则打架。"""
    if not text:
        return []
    found: dict[str, MemoryCandidate] = {}
    normalized = text.replace("，", ",").replace("。", ".")
    for key, pattern, confidence in _RULES:
        if key in found:
            continue
        for match in pattern.finditer(normalized):
            value = (match.group("v") or "").strip(" ,.")
            value = value.rstrip(_TRAILING).strip()
            if key == "pet_age":
                value = _normalize_age(value)
            if not _is_usable(value):
                continue
            found[key] = MemoryCandidate(key=key, value=value, confidence=confidence, quote=match.group(0))
            break
    return list(found.values())


def _normalize_age(value: str) -> str:
    """把「三」转成「3」：下游展示与比较统一用阿拉伯数字。"""
    if value.isdigit():
        return value
    if value.startswith("十"):
        return str(10 + _CN_DIGITS.get(value[1:], 0))
    if len(value) == 2 and value[0] in _CN_DIGITS and value[1] == "十":
        return str(_CN_DIGITS[value[0]] * 10)
    return str(_CN_DIGITS.get(value, value))


def label_of(key: str) -> str:
    return FACT_LABELS.get(key, key)


def _is_usable(value: str) -> bool:
    if not value or len(value) > 20:
        return False
    if value in _STOPWORDS:
        return False
    return value not in {"吗", "呢", "吧", "啊"}
