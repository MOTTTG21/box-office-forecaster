"""Compares this week's industry-wide box office total against the same ISO calendar week in
past years - "is the industry up or down vs. this time of year historically," not just how one
movie performed.

MAX_YEARS_BACK bounds the lookback to a fixed, small window (mirrors comparison_service.py's
MAX_COMPARISON_SERIES bounding philosophy - never an unbounded backfill triggered by one
request). ISO week is used to find "the same week" in past years rather than month/day matching,
since it stays aligned to the actual Mon-Sun box office week; a year without that many ISO weeks
(no week 53) is skipped rather than crashing. A year with no scraped/scrapable data becomes a
point with total_gross_usd=None - never silently treated as 0, which would look like a real
collapse in the industry rather than missing data. The year-over-year percentage itself is
computed client-side (frontend/src/lib/industryHealth.ts), same pattern as weekOverWeek.ts.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.etl.scrape_boxofficemojo_weekend_chart import ingest_industry_weekly_gross
from app.schemas.industry import IndustryHealthComparison, IndustryWeekPoint

MAX_YEARS_BACK = 5


def get_industry_week_over_week_comparison(db: Session, today: date) -> IndustryHealthComparison:
    iso_year, iso_week, _ = today.isocalendar()
    current_week_start = date.fromisocalendar(iso_year, iso_week, 1)
    current_week_end = date.fromisocalendar(iso_year, iso_week, 7)

    points: list[IndustryWeekPoint] = []
    for years_back in range(MAX_YEARS_BACK, -1, -1):
        year = iso_year - years_back
        try:
            week_start = date.fromisocalendar(year, iso_week, 1)
        except ValueError:
            continue  # that year doesn't have this many ISO weeks (e.g. no week 53)

        row = ingest_industry_weekly_gross(db, week_start)
        points.append(
            IndustryWeekPoint(
                year=year,
                week_start_date=week_start,
                total_gross_usd=row.total_gross_usd if row is not None else None,
            )
        )

    return IndustryHealthComparison(
        current_week_start=current_week_start,
        current_week_end=current_week_end,
        points=points,
    )
