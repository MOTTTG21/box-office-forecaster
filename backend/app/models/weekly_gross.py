from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class WeeklyGrossObservation(Base):
    __tablename__ = "weekly_gross_observations"
    __table_args__ = (UniqueConstraint("movie_id", "week_number", "territory", "source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    week_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    territory: Mapped[str] = mapped_column(String(20), nullable=False)
    weekend_gross_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cumulative_gross_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    theater_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship(back_populates="weekly_gross_observations")
