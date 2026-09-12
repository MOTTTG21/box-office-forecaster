"""Compares a studio's weekly aggregate domestic box office (its own tracked slate, not the
parent company's actual revenue) against real weekly closing-price moves in that studio's
publicly traded parent, for studios that have one. Both series are indexed to % change from
the first week either has data, since box office dollars and a stock price live on wildly
different scales - one shared axis, never two, per this app's existing chart conventions.

This is NOT a statistically meaningful correlation and the UI must say so: a studio's theatrical
slate is a small, lumpy fraction of its parent's overall business (streaming, parks, cable,
consumer products, etc.), while the stock price reflects all of that at once. It's an
exploratory overlay, in the same spirit as the "Experimental" buzz-adjusted forecast elsewhere
in the app - not a validated signal.
"""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Movie, WeeklyGrossObservation
from app.schemas.studio import StudioMarketComparison, StudioMarketPoint
from app.services.concurrency import run_with_isolated_sessions
from app.services.stock_price_service import ingest_weekly_stock_prices
from app.services.studio_registry import get_studio


def build_market_points(
    weekly_box_office: dict[date, int], stock_by_week: dict[date, float]
) -> list[StudioMarketPoint]:
    """Pure indexing math over already-fetched weekly series - kept separate from the DB/network
    orchestration below so it's unit-testable without a database or a live Yahoo Finance call."""
    common_weeks = sorted(set(weekly_box_office) & set(stock_by_week))
    if len(common_weeks) < 2:
        return []

    base_box_office = weekly_box_office[common_weeks[0]]
    base_stock = stock_by_week[common_weeks[0]]

    return [
        StudioMarketPoint(
            week_start_date=week,
            box_office_pct_change=(
                (weekly_box_office[week] - base_box_office) / base_box_office * 100 if base_box_office else None
            ),
            stock_pct_change=((stock_by_week[week] - base_stock) / base_stock * 100 if base_stock else None),
        )
        for week in common_weeks
    ]


def _ingest_weekly_gross_by_id(session: Session, movie_id: int) -> None:
    from app.etl.scrape_boxofficemojo import ingest_weekly_gross_from_boxofficemojo

    movie = session.query(Movie).filter(Movie.id == movie_id).one_or_none()
    if movie is not None:
        ingest_weekly_gross_from_boxofficemojo(session, movie)


def _ensure_weekly_gross_ingested(db: Session, slug: str, year: int) -> None:
    movie_ids = [
        movie_id
        for (movie_id,) in db.query(Movie.id)
        .filter(Movie.studio_slug == slug)
        .filter(Movie.release_date.isnot(None))
        .filter(Movie.release_date >= date(year, 1, 1))
        .filter(Movie.release_date <= date(year, 12, 31))
        .filter(Movie.status == "released")
        .all()
    ]
    run_with_isolated_sessions(movie_ids, _ingest_weekly_gross_by_id)


def get_studio_market_comparison(db: Session, slug: str, year: int) -> StudioMarketComparison | None:
    studio = get_studio(slug)
    if studio is None:
        return None

    if studio.ticker is None:
        return StudioMarketComparison(slug=slug, display_name=studio.display_name, ticker=None, year=year, points=[])

    _ensure_weekly_gross_ingested(db, slug, year)

    # WeeklyGrossObservation.week_start_date is Box Office Mojo's own Fri-Thu theatrical week
    # (from the per-movie scraper), not this app's Mon-Sun box office week used elsewhere - both
    # sides are re-keyed to date.fromisocalendar(*, *, 1) so they line up on the same weeks. A
    # wide date range is queried (not the strict calendar year) since a late-December or
    # early-January Friday can belong to an ISO week whose Monday falls in the other year.
    raw_rows = (
        db.query(WeeklyGrossObservation.week_start_date, func.sum(WeeklyGrossObservation.weekend_gross_usd))
        .join(Movie, Movie.id == WeeklyGrossObservation.movie_id)
        .filter(Movie.studio_slug == slug)
        .filter(WeeklyGrossObservation.territory == "domestic")
        .filter(WeeklyGrossObservation.week_start_date.isnot(None))
        .filter(WeeklyGrossObservation.week_start_date >= date(year - 1, 12, 1))
        .filter(WeeklyGrossObservation.week_start_date <= date(year + 1, 1, 31))
        .group_by(WeeklyGrossObservation.week_start_date)
        .all()
    )
    weekly_box_office: dict[date, int] = {}
    for raw_date, total in raw_rows:
        iso_year, iso_week, _ = raw_date.isocalendar()
        monday = date.fromisocalendar(iso_year, iso_week, 1)
        if monday.year == year:
            weekly_box_office[monday] = int(total)

    stock_rows = ingest_weekly_stock_prices(db, studio.ticker)
    stock_by_week = {row.week_start_date: row.close_usd for row in stock_rows if row.week_start_date.year == year}

    points = build_market_points(weekly_box_office, stock_by_week)

    return StudioMarketComparison(
        slug=slug, display_name=studio.display_name, ticker=studio.ticker, year=year, points=points
    )
