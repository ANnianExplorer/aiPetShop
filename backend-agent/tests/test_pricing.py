"""按模型成本估算：只验算术与配置解析，不依赖任何网络/数据库。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.core.pricing import ModelPrice, estimate_cost_usd


def test_estimate_cost_for_one_million_tokens() -> None:
    price = ModelPrice(input_per_mtok=0.27, output_per_mtok=1.10)
    assert estimate_cost_usd(1_000_000, 1_000_000, price) == 1.37


def test_estimate_cost_rounds_to_six_decimals() -> None:
    price = ModelPrice(input_per_mtok=3.0, output_per_mtok=4.0)
    assert estimate_cost_usd(1_000, 2_000, price) == 0.011


def test_unpriced_model_returns_none_not_zero() -> None:
    assert estimate_cost_usd(10_000, 5_000, None) is None


def test_negative_price_rejected() -> None:
    with pytest.raises(ValidationError):
        ModelPrice(input_per_mtok=-0.01, output_per_mtok=1.0)


def test_settings_parses_model_prices_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "PET_AGENT_MODEL_PRICES",
        '{"scripted":{"input_per_mtok":1.0,"output_per_mtok":2.0}}',
    )
    settings = Settings()
    assert settings.model_prices["scripted"].input_per_mtok == 1.0
    assert settings.model_prices["scripted"].output_per_mtok == 2.0


def test_settings_defaults_to_no_prices() -> None:
    assert Settings().model_prices == {}
