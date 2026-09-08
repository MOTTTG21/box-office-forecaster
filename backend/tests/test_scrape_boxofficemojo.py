from pathlib import Path

import httpx

from app.etl.scrape_boxofficemojo import _fetch_weekend_rows

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


def test_empty_table_returns_empty_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>no table here</body></html>")

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com") as client:
        rows = _fetch_weekend_rows(client, "/release/rlXXXX/weekend/", release_year=2023)

    assert rows == []
