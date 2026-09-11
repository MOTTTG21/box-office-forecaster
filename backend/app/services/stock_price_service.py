"""Fetches real weekly closing stock prices for a studio's publicly traded parent company, via
Yahoo Finance's chart endpoint. That endpoint is unofficial (no API key, no published SLA) - the
same "polite external source, ToS risk accepted for a personal/non-commercial project" posture
already used for the Box Office Mojo scraper, chosen over Stooq (which now blocks scripted
requests behind a JS proof-of-work wall) and over signing up for a paid/keyed provider.

Yahoo's weekly bars are anchored to each week's first trading day, which drifts off Monday around
holidays. Every point is re-keyed to date.fromisocalendar(year, week, 1) - the Monday of that
ISO week - so it lines up with the app's own Mon-Sun box office week and with
WeeklyGrossObservation.week_start_date for the studio-vs-market comparison. Yahoo also emits a
second, partial bar for the current in-progress week alongside the prior full one - both
normalize to the same Monday, so points are deduped by week (keeping the later value, i.e. the
more complete one) before they ever reach the database.
"""

from datetime import date, datetime, timezone

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import StudioStockPrice

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
USER_AGENT = "Mozilla/5.0 (compatible; box-office-forecaster/1.0)"
SOURCE = "yahoo_finance"
DEFAULT_RANGE = "2y"


def _fetch_weekly_closes(client: httpx.Client, ticker: str) -> list[tuple[date, float]]:
    response = client.get(
        YAHOO_CHART_URL.format(ticker=ticker),
        params={"interval": "1wk", "range": DEFAULT_RANGE},
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    results = response.json()["chart"]["result"]
    if not results:
        return []

    row = results[0]
    timestamps = row.get("timestamp") or []
    closes = row["indicators"]["quote"][0].get("close") or []

    by_week: dict[date, float] = {}
    for ts, close in zip(timestamps, closes, strict=False):
        if close is None:
            continue
        trade_date = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        iso_year, iso_week, _ = trade_date.isocalendar()
        week_start = date.fromisocalendar(iso_year, iso_week, 1)
        by_week[week_start] = close  # later bar for the same normalized week wins
    return sorted(by_week.items())


def ingest_weekly_stock_prices(db: Session, ticker: str) -> list[StudioStockPrice]:
    """Fetches and caches weekly closes for `ticker`, then returns everything cached for it
    (not just what was fetched this call) so callers always see the full history."""
    with httpx.Client(timeout=10.0) as client:
        try:
            points = _fetch_weekly_closes(client, ticker)
        except httpx.HTTPError:
            points = []

    existing_weeks = {
        row.week_start_date for row in db.query(StudioStockPrice).filter(StudioStockPrice.ticker == ticker).all()
    }

    new_rows = [
        StudioStockPrice(ticker=ticker, week_start_date=week_start, close_usd=close, source=SOURCE)
        for week_start, close in points
        if week_start not in existing_weeks
    ]

    if new_rows:
        db.add_all(new_rows)
        try:
            db.commit()
        except IntegrityError:
            # another request cached the same new weeks between our check and our commit
            db.rollback()

    return (
        db.query(StudioStockPrice)
        .filter(StudioStockPrice.ticker == ticker)
        .order_by(StudioStockPrice.week_start_date)
        .all()
    )
