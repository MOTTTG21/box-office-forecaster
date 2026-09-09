from datetime import date

from app.services import industry_health_service as service_module
from app.services.industry_health_service import MAX_YEARS_BACK, get_industry_week_over_week_comparison


class _FakeRow:
    def __init__(self, total_gross_usd: int):
        self.total_gross_usd = total_gross_usd


def test_ingests_exactly_max_years_back_plus_one_weeks(monkeypatch):
    calls = []

    def fake_ingest(db, week_start):
        calls.append(week_start)
        return _FakeRow(1_000_000)

    monkeypatch.setattr(service_module, "ingest_industry_weekly_gross", fake_ingest)

    get_industry_week_over_week_comparison(db=None, today=date(2026, 9, 8))

    assert len(calls) == MAX_YEARS_BACK + 1


def test_missing_data_becomes_none_not_zero(monkeypatch):
    def fake_ingest(db, week_start):
        return None  # simulates a year BOM couldn't be scraped for

    monkeypatch.setattr(service_module, "ingest_industry_weekly_gross", fake_ingest)

    result = get_industry_week_over_week_comparison(db=None, today=date(2026, 9, 8))

    assert all(p.total_gross_usd is None for p in result.points)


def test_iso_week_53_missing_in_some_years_is_skipped_not_crashed(monkeypatch):
    # 2026-12-28 is ISO week 53 of 2026, a year that actually has one - but plenty of years in
    # the 5-year lookback window won't, and that must not raise
    monkeypatch.setattr(service_module, "ingest_industry_weekly_gross", lambda db, week_start: _FakeRow(1))

    result = get_industry_week_over_week_comparison(db=None, today=date(2026, 12, 28))

    assert len(result.points) <= MAX_YEARS_BACK + 1
    assert len(result.points) >= 1


def test_current_week_bounds_match_todays_iso_week(monkeypatch):
    monkeypatch.setattr(service_module, "ingest_industry_weekly_gross", lambda db, week_start: _FakeRow(1))

    result = get_industry_week_over_week_comparison(db=None, today=date(2026, 9, 8))

    assert result.current_week_start == date(2026, 9, 7)  # Monday of that ISO week
    assert result.current_week_end == date(2026, 9, 13)  # Sunday
