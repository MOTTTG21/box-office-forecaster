from datetime import date

from pydantic import BaseModel


class IndustryWeekPoint(BaseModel):
    year: int
    week_start_date: date
    total_gross_usd: int | None = None


class IndustryHealthComparison(BaseModel):
    current_week_start: date
    current_week_end: date
    points: list[IndustryWeekPoint]
