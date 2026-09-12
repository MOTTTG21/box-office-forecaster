"""Records real per-request latency to request_latency_samples, so the Data Quality page can
show actual P50/P95/P99 instead of a claim. Deliberately not the request's own DB session
(middleware wraps the whole request/response cycle, including error paths, so it needs a
session that outlives and doesn't interfere with whatever the route handler does with its own).

Retention is enforced probabilistically on write (delete anything older than RETENTION_DAYS)
rather than a scheduled job, since this project has no cron infrastructure - cheap enough at
this traffic volume, and avoids the table growing unbounded forever.
"""

import random
import time
from datetime import datetime, timedelta, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.db import SessionLocal
from app.models import RequestLatencySample

EXCLUDED_PATHS = {"/api/health"}
RETENTION_DAYS = 7
PRUNE_PROBABILITY = 0.02


def _retention_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)


class LatencyTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        route = request.scope.get("route")
        route_template = route.path if route is not None else request.url.path

        if route_template not in EXCLUDED_PATHS:
            _record_sample(route_template, request.method, response.status_code, duration_ms)

        return response


def _record_sample(route_template: str, method: str, status_code: int, duration_ms: float) -> None:
    session = SessionLocal()
    try:
        session.add(
            RequestLatencySample(
                method=method, route_template=route_template, status_code=status_code, duration_ms=duration_ms
            )
        )
        if random.random() < PRUNE_PROBABILITY:
            session.execute(
                RequestLatencySample.__table__.delete().where(RequestLatencySample.created_at < _retention_cutoff())
            )
        session.commit()
    except Exception:
        pass  # observability must never break the actual request
    finally:
        session.close()
