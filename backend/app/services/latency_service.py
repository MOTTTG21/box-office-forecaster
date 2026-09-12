"""Reports real P50/P95/P99 request latency per endpoint, computed from
request_latency_samples (written by app.core.latency_middleware on every real request). Uses
Postgres's own percentile_cont ordered-set aggregate rather than pulling every row into Python
and sorting - the database already knows how to do this efficiently.

A route with fewer than MIN_SAMPLES observations in the retention window is left out entirely
rather than shown with a misleadingly precise-looking percentile from 1-2 data points - the same
"not enough data" honesty rule used everywhere else in this app.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.latency_middleware import RETENTION_DAYS
from app.models import RequestLatencySample
from app.schemas.data_quality import EndpointLatencyStats, LatencyReport

MIN_SAMPLES = 5


def get_latency_report(db: Session) -> LatencyReport:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    rows = (
        db.query(
            RequestLatencySample.method,
            RequestLatencySample.route_template,
            func.count().label("sample_count"),
            func.percentile_cont(0.50).within_group(RequestLatencySample.duration_ms).label("p50_ms"),
            func.percentile_cont(0.95).within_group(RequestLatencySample.duration_ms).label("p95_ms"),
            func.percentile_cont(0.99).within_group(RequestLatencySample.duration_ms).label("p99_ms"),
        )
        .filter(RequestLatencySample.created_at >= cutoff)
        .group_by(RequestLatencySample.method, RequestLatencySample.route_template)
        .having(func.count() >= MIN_SAMPLES)
        .order_by(func.percentile_cont(0.95).within_group(RequestLatencySample.duration_ms).desc())
        .all()
    )

    endpoints = [
        EndpointLatencyStats(
            method=row.method,
            route_template=row.route_template,
            sample_count=row.sample_count,
            p50_ms=round(row.p50_ms, 1),
            p95_ms=round(row.p95_ms, 1),
            p99_ms=round(row.p99_ms, 1),
        )
        for row in rows
    ]

    return LatencyReport(retention_days=RETENTION_DAYS, min_samples=MIN_SAMPLES, endpoints=endpoints)
