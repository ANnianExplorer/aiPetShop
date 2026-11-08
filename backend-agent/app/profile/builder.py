"""宠物画像规则：把「已确认的长期事实」聚合成一份可回放的结构化文档。

为什么不用 LLM 写画像：
- 画像会被注入对话上下文、显示在管理端、后续驱动桌宠外观，**错的代价比漏的大**；
- 每条结论都要能指回一条 `memory_fact`，模型自由发挥会让"证据"断链；
- 规则可以穷举测试，模型不行。

因此这里只做**确定性聚合**：没有事实支撑的字段不出现，也不写 "unknown"。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..domain.models import MemoryFact

# 参与画像的 key；与 memory/extract.py 的 FACT_LABELS 保持一致
USED_KEYS: tuple[str, ...] = (
    "pet_name",
    "pet_age",
    "pet_weight",
    "allergy",
    "food_like",
    "food_avoid",
    "vaccine",
)

WEIGHT_UNITS = ("kg", "KG", "公斤", "千克", "斤")


def _evidence(fact: MemoryFact) -> dict[str, object]:
    return {
        "text": f"{fact.key}={fact.value}",
        "factId": fact.id,
        "confidence": round(float(fact.confidence), 2),
    }


def _parse_weight(value: str) -> tuple[float | None, str | None]:
    """把「4.6kg / 4.6公斤 / 9.2斤」解析成 kg 数值；解析不了就原样留着。"""
    text = value.strip()
    lowered = text.lower()
    for unit in WEIGHT_UNITS:
        if lowered.endswith(unit.lower()):
            number = text[: len(text) - len(unit)].strip()
            try:
                weight = float(number)
            except ValueError:
                return None, text
            if unit == "斤":
                weight = weight / 2
            return round(weight, 2), None
    try:
        return round(float(text), 2), None
    except ValueError:
        return None, text


def _days_since(stamp: str | None, now: datetime) -> int | None:
    if not stamp:
        return None
    text = stamp.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            when = datetime.strptime(text[: len(text)], fmt)
        except ValueError:
            continue
        return max(0, (now - when).days)
    return None


@dataclass
class ProfileDocument:
    """画像正文 + 对账数据。`data` 直接入库，字段名与 API 报文一致。"""

    version: int
    data: dict[str, object]
    fact_count: int
    confidence: float
    evidence: list[dict[str, object]] = field(default_factory=list)


def build_profile(
    facts: list[MemoryFact],
    *,
    now: datetime | None = None,
    vaccine_stale_days: int = 300,
) -> dict[str, object]:
    """把事实聚合成画像正文（不含版本，版本由仓储层分配）。

    只消费 `USED_KEYS` 且 `confidence >= 0.7` 的事实；同 key 取置信度最高的一条。
    """
    moment = now or datetime.now(UTC).replace(tzinfo=None)
    picked: dict[str, MemoryFact] = {}
    for fact in facts:
        if fact.key not in USED_KEYS or float(fact.confidence) < 0.7:
            continue
        current = picked.get(fact.key)
        if current is None or float(fact.confidence) > float(current.confidence):
            picked[fact.key] = fact

    basics: dict[str, object] = {}
    traits: dict[str, object] = {}
    preferences: list[dict[str, object]] = []
    risk_flags: list[dict[str, object]] = []
    care_gaps: list[dict[str, object]] = []
    evidence: list[dict[str, object]] = []

    name = picked.get("pet_name")
    if name:
        basics["name"] = name.value
    age = picked.get("pet_age")
    if age:
        basics["age"] = age.value
    weight = picked.get("pet_weight")
    if weight:
        kg, raw = _parse_weight(weight.value)
        if kg is not None:
            basics["weightKg"] = kg
        if raw is not None:
            basics["weightText"] = raw

    allergy = picked.get("allergy")
    if allergy:
        risk_flags.append({"text": f"对{allergy.value}过敏", "evidence": _evidence(allergy)})

    liked = picked.get("food_like")
    if liked:
        preferences.append({"text": f"爱吃：{liked.value}", "evidence": _evidence(liked)})

    avoid = picked.get("food_avoid")
    if avoid:
        traits["appetite"] = "picky"
        preferences.append({"text": f"忌口：{avoid.value}", "evidence": _evidence(avoid)})

    vaccine = picked.get("vaccine")
    if vaccine:
        days = _days_since(vaccine.update_time or vaccine.create_time, moment)
        if days is not None and days > vaccine_stale_days:
            care_gaps.append(
                {
                    "text": f"疫苗记录是 {days} 天前的（{vaccine.value}），建议确认是否要补种",
                    "evidence": _evidence(vaccine),
                }
            )

    for key in USED_KEYS:
        fact = picked.get(key)
        if fact is None:
            continue
        evidence.append(
            {
                "key": fact.key,
                "value": fact.value,
                "confidence": round(float(fact.confidence), 2),
                "factId": fact.id,
            }
        )

    data: dict[str, object] = {"evidence": evidence}
    if basics:
        data["basics"] = basics
    if traits:
        data["traits"] = traits
    if preferences:
        data["preferences"] = preferences
    if risk_flags:
        data["riskFlags"] = risk_flags
    if care_gaps:
        data["careGaps"] = care_gaps

    confidence = (
        round(sum(float(f.confidence) for f in picked.values()) / len(picked), 2) if picked else 0.0
    )
    return {"data": data, "fact_count": len(picked), "confidence": confidence}


def profile_lines(data: dict[str, object], *, limit: int = 2) -> list[str]:
    """注入上下文用的短句：只放「风险」和「待办」，事实本身已经由记忆层注入。"""
    lines: list[str] = []
    risks = data.get("riskFlags") or []
    if isinstance(risks, list):
        texts = [str(item.get("text")) for item in risks if isinstance(item, dict) and item.get("text")]
        if texts:
            lines.append("风险：" + "；".join(texts))
    gaps = data.get("careGaps") or []
    if isinstance(gaps, list):
        texts = [str(item.get("text")) for item in gaps if isinstance(item, dict) and item.get("text")]
        if texts:
            lines.append("待办：" + "；".join(texts))
    return lines[:limit]
