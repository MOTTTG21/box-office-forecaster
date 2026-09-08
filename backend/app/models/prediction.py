from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"), nullable=False, index=True)
    predicted_opening_weekend_usd: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    predicted_domestic_total_usd: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    predicted_worldwide_total_usd: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    predicted_decay_curve: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship(back_populates="predictions")
    model_run: Mapped["ModelRun"] = relationship(back_populates="predictions")
