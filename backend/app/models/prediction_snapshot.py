from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class PredictionSnapshot(Base):
    """One row per (movie, week being predicted, calendar day) - the day-by-day history behind
    the fluctuating forecast chart. Once a day's snapshot is recorded it's never overwritten,
    so what gets charted for "today" always matches what visitors were actually shown that day.
    See app/services/prediction_snapshot_service.py.
    """

    __tablename__ = "prediction_snapshots"
    __table_args__ = (UniqueConstraint("movie_id", "week_number", "snapshot_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_new_release: Mapped[bool] = mapped_column(Boolean, nullable=False)
    predicted_weekend_gross_usd: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship()
