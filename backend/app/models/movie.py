from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    rotten_tomatoes_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metascore: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imdb_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    critic_scores_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    genres: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    belongs_to_collection_tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_sequel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    poster_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    popularity_tmdb_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    popularity_snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    demographic_percent_female: Mapped[float | None] = mapped_column(Float, nullable=True)
    demographic_percent_male: Mapped[float | None] = mapped_column(Float, nullable=True)
    demographic_percent_under_25: Mapped[float | None] = mapped_column(Float, nullable=True)
    demographic_percent_25_and_over: Mapped[float | None] = mapped_column(Float, nullable=True)
    demographic_race_breakdown: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    demographic_source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    demographics_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    studio_slug: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    credits: Mapped[list["MovieCredit"]] = relationship(back_populates="movie")
    weekly_gross_observations: Mapped[list["WeeklyGrossObservation"]] = relationship(back_populates="movie")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="movie")
