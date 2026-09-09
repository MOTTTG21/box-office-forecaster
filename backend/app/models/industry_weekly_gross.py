from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class IndustryWeeklyGross(Base):
    """The domestic box office industry's total gross for one Mon-Sun week - not a source-
    reported aggregate (Box Office Mojo's weekend-chart pages don't publish one), but the sum
    of that page's per-movie "Gross" column. Documented as a less-authoritative fallback in
    app/etl/scrape_boxofficemojo_weekend_chart.py.
    """

    __tablename__ = "industry_weekly_gross"
    __table_args__ = (UniqueConstraint("week_start_date", "source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_gross_usd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
