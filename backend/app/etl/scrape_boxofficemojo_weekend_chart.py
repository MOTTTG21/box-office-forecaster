"""Scrapes Box Office Mojo's aggregate weekend-chart pages (/weekend/<YEAR>W<WW>/) - a
different page family from the per-movie weekly-breakdown pages scrape_boxofficemojo.py already
handles (/release/rlXXXX/weekend/). URL pattern and DOM structure verified live 2026-09-08
against a real page (see backend/tests/fixtures/bom_weekend_chart_2026w36.html) before writing
any of this.

There is no single aggregate-total figure on this page type - confirmed by searching the real
page for one and finding only per-movie "Total Gross" (lifetime) columns. The industry weekend
total here is the sum of the table's per-movie "Gross" (this weekend) column - a documented,
less-authoritative fallback, not a source-reported number. That distinction matters: this is an
estimate derived from real data, not itself a number Box Office Mojo publishes.
"""

from datetime import date, timedelta

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.etl.scrape_boxofficemojo import BOM_BASE_URL, USER_AGENT, _parse_money
from app.models import IndustryWeeklyGross

SOURCE = "boxofficemojo_weekend_chart_sum"


def _fetch_weekend_chart_total(client: httpx.Client, iso_year: int, iso_week: int) -> int | None:
    response = client.get(f"/weekend/{iso_year}W{iso_week:02d}/")
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="mojo-body-table")
    if table is None:
        return None

    rows = table.find_all("tr")[1:]  # skip header
    total = 0
    found_any = False
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        gross = _parse_money(cells[3].get_text(strip=True))
        if gross is not None:
            total += gross
            found_any = True

    return total if found_any else None


def ingest_industry_weekly_gross(db: Session, week_start: date) -> IndustryWeeklyGross | None:
    """Scrapes and stores the industry-wide weekend total for the Mon-Sun week starting on
    `week_start`. Cache-first, same shape as ingest_weekly_gross_from_boxofficemojo: checks the
    DB before hitting BOM at all."""
    existing = (
        db.query(IndustryWeeklyGross)
        .filter(IndustryWeeklyGross.week_start_date == week_start, IndustryWeeklyGross.source == SOURCE)
        .one_or_none()
    )
    if existing is not None:
        return existing

    iso_year, iso_week, _ = week_start.isocalendar()

    with httpx.Client(base_url=BOM_BASE_URL, headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        total = _fetch_weekend_chart_total(client, iso_year, iso_week)

    if total is None:
        return None

    row = IndustryWeeklyGross(
        week_start_date=week_start,
        week_end_date=week_start + timedelta(days=6),
        total_gross_usd=total,
        source=SOURCE,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
