"""情景记忆：把用户说过的「已经发生的事」抽成一段可召回的往事。

边界（与事实记忆一致，测试盯着）：
1. 只抽用户明确说过已经发生的事；问句、否定句、习惯句不抽；
2. 一条消息最多产出一个情景，事件类型按 `EPISODE_KINDS` 的顺序取第一个命中；
3. 发生时间只精确到日，时间部分固定 `00:00:00`；相对时间按自然日近似；
4. 召回是确定性规则打分，不依赖向量库；召回失败不影响对话主链路。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from ..domain.models import MemoryEpisode

# 顺序即优先级：一句话里出现多个事件词时，记第一个。
EPISODE_KINDS: dict[str, str] = {
    "bath": "洗澡",
    "deworm": "驱虫",
    "vaccine": "疫苗",
    "checkup": "体检",
    "vet": "就医",
    "neuter": "绝育",
    "grooming": "美容",
    "nails": "剪指甲",
    "vomit": "呕吐",
    "diarrhea": "腹泻",
}

_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("bath", ("洗澡", "泡澡", "洗了澡", "洗个澡")),
    ("deworm", ("驱虫",)),
    ("vaccine", ("疫苗", "打针", "接种")),
    ("checkup", ("体检", "复查")),
    ("vet", ("去医院", "看病", "就诊", "看医生", "挂号")),
    ("neuter", ("绝育",)),
    ("grooming", ("美容", "剃毛", "剪毛")),
    ("nails", ("剪指甲", "修指甲")),
    ("vomit", ("呕吐", "吐了", "吐过")),
    ("diarrhea", ("拉稀", "腹泻", "软便", "拉肚子")),
)

_QUESTION_MARKERS = ("?", "？", "吗", "什么", "啥", "哪", "怎么", "多少", "是否", "多久")
_NEGATION_MARKERS = ("没", "未", "不用", "不要", "不需要", "还没")
_COMPLETION_MARKERS = ("了", "过", "刚", "已经")
_CN_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}
_SPACE_RE = re.compile(r"\s+")
_NUMBER_RE = r"(\d{1,2}|[一二两三四五六七八九十])"
_DAYS_AGO_RE = re.compile(_NUMBER_RE + r"\s*天前")
_WEEKS_AGO_RE = re.compile(_NUMBER_RE + r"\s*(?:周|个?星期)前")
_MONTHS_AGO_RE = re.compile(_NUMBER_RE + r"\s*个?月前")
_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")

# 召回阈值：0.55×类型命中 + 0.35×字符重叠 + 0.10×新鲜度。
# 阈值 0.50 意味着「事件类型必须命中」——只有时间/宠物名等碎词重合不会触发注入。
RECALL_THRESHOLD = 0.50
_RECENCY_DAYS = 90


@dataclass(frozen=True)
class EpisodeCandidate:
    kind: str
    label: str
    summary: str
    occurred_at: str
    time_word: str


def label_of_kind(kind: str) -> str:
    return EPISODE_KINDS.get(kind, kind)


def extract_episode(text: str, *, now: datetime | None = None) -> EpisodeCandidate | None:
    """从一句用户消息里抽情景；没有可记的内容返回 None。"""
    raw = _SPACE_RE.sub(" ", (text or "")).strip()
    if not raw or _looks_like_question(raw) or _is_negated(raw):
        return None
    kind = _match_kind(raw)
    if kind is None:
        return None

    moment = now or datetime.now()
    relative = _relative_date(raw, moment)
    if relative is None and not any(marker in raw for marker in _COMPLETION_MARKERS):
        # 没有时间词、也没有「了/过/刚/已经」：更像习惯（"它洗澡特别乖"），不记。
        return None
    occurred, time_word = relative or (moment.date(), "今天")
    occurred_at = datetime.combine(occurred, datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
    return EpisodeCandidate(
        kind=kind,
        label=label_of_kind(kind),
        summary=raw[:180],
        occurred_at=occurred_at,
        time_word=time_word,
    )


def score_episode(
    question: str, episode: MemoryEpisode, *, now: datetime | None = None
) -> float:
    """问题与往事的相关度：事件类型命中是主信号，字符重叠只用于排序。"""
    kind_hit = 1.0 if _kind_hit(question, episode) else 0.0
    overlap = _char_overlap(question, episode.summary)
    recency = _recency(episode.occurred_at, now or datetime.now())
    return round(0.55 * kind_hit + 0.35 * overlap + 0.10 * recency, 4)


def select_episodes(
    question: str,
    episodes: list[MemoryEpisode],
    *,
    limit: int = 3,
    now: datetime | None = None,
) -> list[MemoryEpisode]:
    """按相关度取前 N 条；同分时新的优先。"""
    if limit <= 0:
        return []
    scored = [(score_episode(question, episode, now=now), episode) for episode in episodes]
    scored.sort(
        key=lambda pair: (pair[0], pair[1].occurred_at or "", pair[1].id),
        reverse=True,
    )
    return [episode for score, episode in scored if score >= RECALL_THRESHOLD][:limit]


def format_episode_line(episode: MemoryEpisode) -> str:
    """给模型读的一行：日期 + 类型 + 原话 + 来源消息 id。"""
    day = (episode.occurred_at or "")[:10]
    head = f"{day}（{label_of_kind(episode.kind)}）：{episode.summary}" if day else (
        f"（{label_of_kind(episode.kind)}）：{episode.summary}"
    )
    line = f"- {head}"
    if episode.source_message_id:
        line += f"（来源消息 {episode.source_message_id}）"
    return line


def _looks_like_question(text: str) -> bool:
    if text.endswith(("?", "？")):
        return True
    return any(marker in text for marker in _QUESTION_MARKERS)


def _is_negated(text: str) -> bool:
    return any(marker in text for marker in _NEGATION_MARKERS)


def _match_kind(text: str) -> str | None:
    for kind, aliases in _ALIASES:
        if any(alias in text for alias in aliases):
            return kind
    return None


def _relative_date(text: str, now: datetime) -> tuple[date, str] | None:
    today = now.date()
    # 「上上个月」包含「上个月」，「上上周」包含「上周」：长的必须排在前面。
    fixed: tuple[tuple[str, int], ...] = (
        ("大前天", 3),
        ("前天", 2),
        ("昨天", 1),
        ("上上个月", 60),
        ("上个月", 30),
        ("半个月前", 15),
        ("上上周", 14),
        ("上周", 7),
        ("上星期", 7),
    )
    for word, days in fixed:
        if word in text:
            return today - timedelta(days=days), word
    for word in ("今天", "刚才", "刚刚"):
        if word in text:
            return today, "今天"
    for pattern, unit_days, label in (
        (_DAYS_AGO_RE, 1, "天前"),
        (_WEEKS_AGO_RE, 7, "周前"),
        (_MONTHS_AGO_RE, 30, "个月前"),
    ):
        match = pattern.search(text)
        if match is None:
            continue
        amount = _parse_number(match.group(1))
        if amount is not None:
            return today - timedelta(days=amount * unit_days), f"{match.group(1)}{label}"
    return None


def _parse_number(raw: str) -> int | None:
    if raw.isdigit():
        return int(raw)
    return _CN_NUMBERS.get(raw)


def _kind_hit(question: str, episode: MemoryEpisode) -> bool:
    if label_of_kind(episode.kind) in question:
        return True
    for kind, aliases in _ALIASES:
        if kind == episode.kind and any(alias in question for alias in aliases):
            return True
    return False


def _char_overlap(question: str, summary: str) -> float:
    left = set(_CHAR_RE.findall(question))
    right = set(_CHAR_RE.findall(summary))
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _recency(occurred_at: str, now: datetime) -> float:
    try:
        occurred = datetime.strptime((occurred_at or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return 0.0
    days = max(0, (now.date() - occurred).days)
    return max(0.0, 1.0 - days / _RECENCY_DAYS)
