from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.db import Base


class RequestLatencySample(Base):
    """One real request's timing, written by app.core.latency_middleware on every API request
    (except health checks). route_template is the route's path pattern (e.g.
    "/api/movies/{tmdb_id}"), never the raw path with real ids in it - otherwise every distinct
    movie/person id would fragment into its own row group and the table would grow unbounded
    instead of converging on a stable set of routes.
    """

    __tablename__ = "request_latency_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    route_template: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
