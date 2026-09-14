from datetime import date, timedelta
from pathlib import Path

import httpx

from app.etl import scrape_boxofficemojo as bom_module
from app.etl.scrape_boxofficemojo import (
    _fetch_weekend_rows,
    _parse_int,
    _parse_money,
    ingest_weekly_gross_from_boxofficemojo,
)
from app.models import Movie, WeeklyGrossObservation

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _client_serving(html_path: Path) -> httpx.Client:
    html = html_path.read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com")


def test_parses_real_weekend_table():
    with _client_serving(FIXTURES_DIR / "bom_weekend_oppenheimer.html") as client:
        rows = _fetch_weekend_rows(client, "/release/rl3725886209/weekend/", release_year=2023)

    assert len(rows) > 0
    first = rows[0]
    assert first["week_number"] == 1
    assert first["weekend_gross_usd"] == 82_455_420
    assert first["cumulative_gross_usd"] == 82_455_420
    assert first["theater_count"] == 3610


def test_week_numbers_are_sequential_and_unique():
    with _client_serving(FIXTURES_DIR / "bom_weekend_oppenheimer.html") as client:
        rows = _fetch_weekend_rows(client, "/release/rl3725886209/weekend/", release_year=2023)

    week_numbers = [r["week_number"] for r in rows]
    assert len(week_numbers) == len(set(week_numbers)), "week numbers must be unique - this guards a real bug"


def test_year_rolls_over_across_multiple_calendar_years():
    # Oppenheimer's real run spans mid-2023 into 2025 (award-season re-release)
    with _client_serving(FIXTURES_DIR / "bom_weekend_oppenheimer.html") as client:
        rows = _fetch_weekend_rows(client, "/release/rl3725886209/weekend/", release_year=2023)

    years_seen = {r["week_start_date"].year for r in rows if r["week_start_date"]}
    assert years_seen == {2023, 2024, 2025}


def test_holiday_occasion_row_is_skipped_not_double_counted():
    # Real bug: D&D's BOM table has a supplementary "Easter wknd" row layered on top of a
    # regular week's row for the same date range - without the /occasion/ link skip, this
    # produced a duplicate week_number and violated the DB's unique constraint.
    with _client_serving(FIXTURES_DIR / "bom_weekend_dnd_holiday_row.html") as client:
        rows = _fetch_weekend_rows(client, "/release/rl1879410177/weekend/", release_year=2023)

    week_numbers = [r["week_number"] for r in rows]
    assert len(week_numbers) == len(set(week_numbers))
    # the real weekend row for that date (not the holiday duplicate) should be present
    assert any(r["week_number"] == 2 and r["weekend_gross_usd"] == 13_881_006 for r in rows)


def test_parse_money_handles_normal_values():
    assert _parse_money("$1,234,567") == 1_234_567
    assert _parse_money("-") is None
    assert _parse_money("") is None


def test_parse_money_returns_none_on_unexpected_markup_instead_of_raising():
    # real risk: a BOM markup change puts non-numeric text in a money cell (e.g. a footnote
    # marker or "TBD") - one odd cell shouldn't take down the whole movie's ingestion
    assert _parse_money("TBD") is None
    assert _parse_money("$--") is None


def test_parse_int_returns_none_on_unexpected_markup_instead_of_raising():
    assert _parse_int("n/a") is None
    assert _parse_int("3,610") == 3610


def test_empty_table_returns_empty_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>no table here</body></html>")

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com") as client:
        rows = _fetch_weekend_rows(client, "/release/rlXXXX/weekend/", release_year=2023)

    assert rows == []


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._result)


class _FakeSession:
    """Enough of the SQLAlchemy Session surface for ingest_weekly_gross_from_boxofficemojo -
    no real database needed to exercise its caching/merge/failure-fallback logic."""

    def __init__(self, existing_rows):
        self.existing_rows = existing_rows
        self.added: list[WeeklyGrossObservation] = []
        self.committed = False
        self.rolled_back = False

    def query(self, _model):
        return _FakeQuery(self.existing_rows)

    def add_all(self, objs):
        self.added.extend(objs)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):
        pass


def _movie() -> Movie:
    return Movie(id=1, tmdb_id=1, title="Test Movie", imdb_id="tt123", release_date=date(2026, 7, 1))


def _row(week_number: int, week_start_date: date, gross: int = 1_000_000) -> WeeklyGrossObservation:
    return WeeklyGrossObservation(
        movie_id=1,
        week_number=week_number,
        week_start_date=week_start_date,
        territory="domestic",
        source="boxofficemojo_scrape",
        weekend_gross_usd=gross,
    )


def test_fresh_cached_data_skips_rescraping_entirely(monkeypatch):
    existing = [_row(6, date.today() - timedelta(days=2))]
    session = _FakeSession(existing)

    def _fail(fn):
        raise AssertionError("should not scrape when cache is still fresh")

    monkeypatch.setattr(bom_module._breaker, "call", _fail)

    result = ingest_weekly_gross_from_boxofficemojo(session, _movie())

    assert result == existing


def test_stale_cached_data_rescrapes_and_merges_the_new_week(monkeypatch):
    # Real bug: a holdover movie's weekly gross used to freeze at whatever week was first
    # looked up, because the old code skipped re-scraping the moment ANY row existed - forever.
    existing = [_row(6, date.today() - timedelta(days=10))]
    session = _FakeSession(existing)
    new_row = {
        "week_number": 7,
        "week_start_date": date.today(),
        "rank": 2,
        "weekend_gross_usd": 8_400_000,
        "theater_count": 3303,
        "cumulative_gross_usd": 935_170_888,
    }
    monkeypatch.setattr(bom_module._breaker, "call", lambda fn: [new_row])

    result = ingest_weekly_gross_from_boxofficemojo(session, _movie())

    assert session.committed is True
    assert {o.week_number for o in result} == {6, 7}


def test_already_known_weeks_are_not_reinserted_on_a_rescrape(monkeypatch):
    # BOM's table always returns every week, not just the new ones - re-inserting a week we
    # already have would violate the (movie_id, week_number, territory, source) unique constraint.
    existing = [_row(6, date.today() - timedelta(days=10))]
    session = _FakeSession(existing)
    monkeypatch.setattr(
        bom_module._breaker,
        "call",
        lambda fn: [
            {
                "week_number": 6,
                "week_start_date": date.today() - timedelta(days=10),
                "rank": 1,
                "weekend_gross_usd": 18_000_000,
                "theater_count": 3520,
                "cumulative_gross_usd": 900_000_000,
            },
            {
                "week_number": 7,
                "week_start_date": date.today(),
                "rank": 2,
                "weekend_gross_usd": 8_400_000,
                "theater_count": 3303,
                "cumulative_gross_usd": 935_170_888,
            },
        ],
    )

    result = ingest_weekly_gross_from_boxofficemojo(session, _movie())

    assert len(session.added) == 1
    assert session.added[0].week_number == 7
    assert {o.week_number for o in result} == {6, 7}


def test_scrape_failure_falls_back_to_existing_data_instead_of_raising(monkeypatch):
    # Several call sites don't wrap this in their own try/except - it must degrade gracefully
    # on its own rather than taking down the whole request.
    existing = [_row(6, date.today() - timedelta(days=10))]
    session = _FakeSession(existing)

    def _raise(fn):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(bom_module._breaker, "call", _raise)

    result = ingest_weekly_gross_from_boxofficemojo(session, _movie())

    assert result == existing
    assert session.committed is False
