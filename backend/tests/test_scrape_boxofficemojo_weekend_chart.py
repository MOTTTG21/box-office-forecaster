from pathlib import Path

import httpx

from app.etl.scrape_boxofficemojo_weekend_chart import _fetch_weekend_chart_total

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _client_serving(html_path: Path) -> httpx.Client:
    html = html_path.read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com")


def test_parses_real_weekend_chart_and_sums_the_gross_column():
    # real fixture: Box Office Mojo's 2026 Weekend 36 chart (Labor Day weekend, Sept 4-6 2026).
    # Reference total independently computed by summing the same real page's "Gross" column by
    # hand before writing this test: $92,475,612 across 60 movies.
    with _client_serving(FIXTURES_DIR / "bom_weekend_chart_2026w36.html") as client:
        total = _fetch_weekend_chart_total(client, iso_year=2026, iso_week=36)

    assert total == 92_475_612


def test_no_table_on_the_page_returns_none():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>no table here</body></html>")

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com") as client:
        total = _fetch_weekend_chart_total(client, iso_year=2026, iso_week=36)

    assert total is None


def test_non_200_response_returns_none():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com") as client:
        total = _fetch_weekend_chart_total(client, iso_year=2099, iso_week=53)

    assert total is None


def test_skips_rows_with_no_parseable_gross():
    html = """
    <table class="mojo-body-table">
      <tr><th>Rank</th><th>LW</th><th>Release</th><th>Gross</th></tr>
      <tr><td>1</td><td>-</td><td>Movie A</td><td>$1,000,000</td></tr>
      <tr><td>2</td><td>-</td><td>Movie B</td><td>-</td></tr>
      <tr><td>3</td><td>-</td><td>Movie C</td><td>$2,000,000</td></tr>
    </table>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://www.boxofficemojo.com") as client:
        total = _fetch_weekend_chart_total(client, iso_year=2026, iso_week=1)

    assert total == 3_000_000
