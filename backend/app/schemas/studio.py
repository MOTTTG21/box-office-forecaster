from datetime import date

from pydantic import BaseModel


class StudioSlateSummary(BaseModel):
    slug: str
    display_name: str
    ticker: str | None = None
    release_count: int
    movies_with_data: int
    total_budget_usd: int | None = None
    total_worldwide_gross_usd: int | None = None
    estimated_profit_usd: int | None = None


class StudioSlateReport(BaseModel):
    year: int
    studios: list[StudioSlateSummary]


class StudioMarketPoint(BaseModel):
    week_start_date: date
    box_office_pct_change: float | None = None
    stock_pct_change: float | None = None


class StudioMarketComparison(BaseModel):
    slug: str
    display_name: str
    ticker: str | None = None
    year: int
    points: list[StudioMarketPoint]
