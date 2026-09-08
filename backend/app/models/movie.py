from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    original_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="upcoming")
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    domestic_gross_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    worldwide_gross_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    genres: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    belongs_to_collection_tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_sequel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    poster_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    popularity_tmdb_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    popularity_snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    credits: Mapped[list["MovieCredit"]] = relationship(back_populates="movie")
    weekly_gross_observations: Mapped[list["WeeklyGrossObservation"]] = relationship(back_populates="movie")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="movie")
