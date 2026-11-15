"""记忆抽取：规则优先，模型只在「结构化不了的闲聊」里才兜底（S2 才开）。

为什么不用 LLM 抽取：宠物档案里的关键事实（名字、过敏、忌口、体重、年龄）都是
模式极其固定的短句，正则的准确率和成本都碾压一次模型调用；而 LLM 抽取的错误会以
「自信的假事实」形式长期污染记忆，比漏抽危险得多。

每条规则只输出「这一个 span 就是事实值」，不做推理（推理交给业务层）。

**精确率优先的三条硬规矩**（S1.27 用 47 条标注用例量出来的，见 evals/cases.jsonl）：
1. 触发词被否定就不要这条事实：`不叫`、`不过敏`、`没对X过敏`、`不爱吃`；
2. 疑问句不抽：`它叫啥`、`它叫什么名字`——问句里的「叫」后面跟的是疑问词，不是名字；
3. `喜欢X` 不再单独成规则：`我喜欢小猫` 会被抽成 `food_like=小猫`。食物偏好必须带
   吃的动词（`爱吃` / `喜欢吃` / `爱啃`），宁可漏抽一句口语，也不往档案里写假事实。
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

# 否定词紧贴在触发词前面时，整条事实不成立（「不叫」「没对…过敏」）。
# 不含「别」：它既是否定又是「特别/分别」的一部分，误伤（「特别喜欢吃」）比漏判更常见
_NEG_BEFORE = r"(?<![不没未非])"
# 问句里的「叫」后面接的是疑问词，不是名字
_QUESTION_HEAD = r"(?!什么|啥|谁|哪|几点|多少)"

_RULES: list[tuple[str, re.Pattern[str], float]] = [
    # 「我家猫叫 Lumina」「名字叫咪咪」；「它叫啥」「它叫什么名字」不算
    (
        "pet_name",
        re.compile(
            rf"{_NEG_BEFORE}(?:名字叫|名叫|叫)\s*{_QUESTION_HEAD}"
            r"(?P<v>[\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z·]{0,11})"
        ),
        0.85,
    ),
    ("pet_age", re.compile(rf"(?P<v>\d{{1,2}})\s*{AGE_UNIT}"), 0.9),
    # 「三岁」「两岁半」：中文数字在口语里比阿拉伯数字更常见
    ("pet_age", re.compile(rf"(?P<v>[一二两三四五六七八九十]{{1,2}})\s*{AGE_UNIT}"), 0.85),
    ("pet_weight", re.compile(rf"(?P<v>\d{{1,2}}(?:\.\d)?)\s*{WEIGHT_UNIT}"), 0.9),
    ("allergy", re.compile(rf"{_NEG_BEFORE}对(?P<v>[\u4e00-\u9fa5]{{1,8}})过敏"), 0.95),
    ("food_avoid", re.compile(r"(?:不吃|不能吃|忌口|别喂)(?P<v>[\u4e00-\u9fa5]{1,8})"), 0.9),
    # 必须带吃/啃/喝的动词：裸「喜欢X」会把「我喜欢小猫」写成食物偏好
    (
        "food_like",
        re.compile(
            rf"{_NEG_BEFORE}(?:爱吃|喜欢(?:吃|啃|喝|舔)|爱啃|爱喝)"
            r"(?P<v>[\u4e00-\u9fa5]{1,8})"
        ),
        0.75,
    ),
    ("vaccine", re.compile(r"(?:打了|接种了|打过)(?P<v>[\u4e00-\u9fa5A-Za-z0-9·\- ]{2,20})(?:疫苗|针)"), 0.85),
]

# 句尾语气词不属于事实值：「改名叫小月亮了」不能把「了」存进名字
_TRAILING = "了的呀哦呢吧啊哈嘛"

# 过敏值上的程度副词：「对花生有点过敏」的事实值是「花生」
_TRAILING_ADVERBS = ("有点", "有一点", "稍微", "些微", "可能", "应该", "一些", "一点")

# 忌口句式里的人称与动词：「别喂它吃洋葱」的事实值是「洋葱」
_LEADING_PRONOUNS = ("它", "他", "她", "我", "你", "们")
_LEADING_VERBS = ("吃", "喂")

# 事实值以这些字收尾说明这句话是否定（「对鸡肉不过敏」→「鸡肉不」）
_NEG_TAIL = "不没未非"

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
            value = _clean_value(key, (match.group("v") or "").strip(" ,."))
            if value is None:
                continue
            if key == "pet_age":
                value = _normalize_age(value)
            if not _is_usable(value):
                continue
            found[key] = MemoryCandidate(key=key, value=value, confidence=confidence, quote=match.group(0))
            break
    return list(found.values())


def _clean_value(key: str, value: str) -> str | None:
    """把「值」剪成事实本身；返回 None 表示这条命中其实是噪声或否定句。"""
    value = value.strip(_TRAILING).strip()
    if key == "allergy":
        value = _strip_suffix(value, _TRAILING_ADVERBS)
    if key == "food_avoid":
        value = _strip_prefix(value, _LEADING_PRONOUNS)
        value = _strip_prefix(value, _LEADING_VERBS)
    if not value:
        return None
    # 「对鸡肉不过敏」：值末尾的「不/没/未/非」说明整句是否定，事实不成立
    if value[-1] in _NEG_TAIL:
        return None
    return value


def _strip_suffix(value: str, suffixes: tuple[str, ...]) -> str:
    changed = True
    while changed and value:
        changed = False
        for suffix in suffixes:
            if len(value) > len(suffix) and value.endswith(suffix):
                value = value[: -len(suffix)]
                changed = True
                break
    return value


def _strip_prefix(value: str, prefixes: tuple[str, ...]) -> str:
    changed = True
    while changed and value:
        changed = False
        for prefix in prefixes:
            if len(value) > len(prefix) and value.startswith(prefix):
                value = value[len(prefix):]
                changed = True
                break
    return value


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
