from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class StudioStockPrice(Base):
    """A real weekly closing price for a studio's publicly traded parent company (see
    app/services/stock_price_service.py for the source and the Monday-of-ISO-week normalization
    that keeps this aligned with the app's own Mon-Sun box office week).
    """

    __tablename__ = "studio_stock_prices"
    __table_args__ = (UniqueConstraint("ticker", "week_start_date", "source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_usd: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
