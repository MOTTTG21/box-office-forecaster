from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class DataAnomaly(Base):
    __tablename__ = "data_anomalies"
    __table_args__ = (UniqueConstraint("movie_id", "rule_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Cross-referenced against real sources (Box Office Mojo, Wikipedia, IMDb) - a suggestion for
    # a human to review on the Data Quality page, never applied automatically. See
    # app/services/anthropic_client.py's investigate_anomaly and the ANOMALY_INVESTIGATION_
    # SYSTEM_PROMPT for the "report what you find, never invent a fix" boundary.
    likely_data_error: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    suggested_correction: Mapped[str | None] = mapped_column(Text, nullable=True)
    investigation_source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    investigated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship()
