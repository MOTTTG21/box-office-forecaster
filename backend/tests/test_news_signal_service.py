from decimal import Decimal

import httpx
import pytest

from app.services import anthropic_client as anthropic_client_module
from app.services.news_signal_service import MAX_ADJUSTMENT_PCT, apply_news_adjustment


def test_returns_none_when_base_prediction_is_none(monkeypatch):
    monkeypatch.setattr(
        anthropic_client_module.anthropic_client, "research_news_adjustment", lambda title: (10.0, "buzz")
    )
    adjusted, reason = apply_news_adjustment(None, "Some Movie")
    assert adjusted is None
    assert reason is None


def test_applies_a_positive_adjustment(monkeypatch):
    monkeypatch.setattr(
        anthropic_client_module.anthropic_client,
        "research_news_adjustment",
        lambda title: (10.0, "Trailer went viral this week."),
    )
    adjusted, reason = apply_news_adjustment(100.0, "Some Movie")
    assert adjusted == pytest.approx(110.0)
    assert reason == "Trailer went viral this week."


def test_clamps_an_extreme_adjustment_to_the_safety_rail(monkeypatch):
    monkeypatch.setattr(
        anthropic_client_module.anthropic_client,
        "research_news_adjustment",
        lambda title: (999.0, "wildly overconfident claim"),
    )
    adjusted, _ = apply_news_adjustment(100.0, "Some Movie")
    assert adjusted == pytest.approx(100.0 * (1 + MAX_ADJUSTMENT_PCT / 100))


def test_clamps_a_negative_extreme_too(monkeypatch):
    monkeypatch.setattr(
        anthropic_client_module.anthropic_client, "research_news_adjustment", lambda title: (-999.0, "disaster")
    )
    adjusted, _ = apply_news_adjustment(100.0, "Some Movie")
    assert adjusted == pytest.approx(100.0 * (1 - MAX_ADJUSTMENT_PCT / 100))


def test_falls_back_to_base_prediction_when_claude_never_calls_the_tool(monkeypatch):
    monkeypatch.setattr(anthropic_client_module.anthropic_client, "research_news_adjustment", lambda title: None)
    adjusted, reason = apply_news_adjustment(100.0, "Some Movie")
    assert adjusted == 100.0
    assert reason is None


def test_accepts_a_decimal_base_prediction_without_crashing(monkeypatch):
    # real bug this guards against: new-release predictions come straight from a SQLAlchemy
    # Numeric column (decimal.Decimal), not a plain float like holdover predictions - Decimal *
    # float raises TypeError, which took /this-week down in production
    monkeypatch.setattr(
        anthropic_client_module.anthropic_client,
        "research_news_adjustment",
        lambda title: (10.0, "Trailer went viral this week."),
    )
    adjusted, reason = apply_news_adjustment(Decimal("100.0"), "Some Movie")
    assert adjusted == pytest.approx(110.0)
    assert isinstance(adjusted, float)
    assert reason == "Trailer went viral this week."


def test_falls_back_to_base_prediction_when_the_api_call_fails(monkeypatch):
    def _raise(title: str):
        raise httpx.HTTPStatusError("boom", request=httpx.Request("POST", "https://x"), response=httpx.Response(500))

    monkeypatch.setattr(anthropic_client_module.anthropic_client, "research_news_adjustment", _raise)
    adjusted, reason = apply_news_adjustment(100.0, "Some Movie")
    assert adjusted == 100.0
    assert reason is None
