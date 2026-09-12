from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class BacktestPrediction(Base):
    """One movie's row from the last run of `python -m app.ml.evaluate --save`
    (app/ml/evaluate.py). Backtesting touches every wide-release movie with a known budget and
    calls TMDB for each one's director history with no caching on that specific call - running it
    live on every page view would repeat the exact mistake already fixed once this session for
    the Studios endpoint (slow, uncached, request-time-unbounded external calls). So it's a
    batch step whose output is cached here, and computed_at on the rows tells the read side how
    fresh the report is - the full table is replaced (delete then insert) on every run, not
    appended to, since this reports "the model as it stands today," not history over past runs.
    """

    __tablename__ = "backtest_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_usd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actual_opening_weekend_usd: Mapped[int] = mapped_column(BigInteger, nullable=False)
    predicted_opening_weekend_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    comp_method: Mapped[str] = mapped_column(String(20), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
