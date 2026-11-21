"""模型单价与成本估算：只做展示级估算，不承诺账单级精度。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelPrice(BaseModel):
    """USD / 1M tokens；两项都可为 0，表示该方向不收费。"""

    input_per_mtok: float = Field(default=0.0, ge=0)
    output_per_mtok: float = Field(default=0.0, ge=0)


def estimate_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    price: ModelPrice | None,
) -> float | None:
    """按 token 数估算成本；未配置单价时返回 None，而不是 0。"""
    if price is None:
        return None
    cost = (
        prompt_tokens * price.input_per_mtok
        + completion_tokens * price.output_per_mtok
    ) / 1_000_000
    return round(cost, 6)
