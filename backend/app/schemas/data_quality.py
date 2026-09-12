from datetime import datetime

from pydantic import BaseModel


class DataAnomalyOut(BaseModel):
    tmdb_id: int
    title: str
    poster_path: str | None = None
    rule_name: str
    severity: str
    detail: str
    ai_explanation: str | None = None
    detected_at: datetime


class EndpointLatencyStats(BaseModel):
    method: str
    route_template: str
    sample_count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float


class LatencyReport(BaseModel):
    retention_days: int
    min_samples: int
    endpoints: list[EndpointLatencyStats]


class CircuitBreakerStatus(BaseModel):
    name: str
    state: str
    consecutive_failures: int
    failure_threshold: int
    total_trips: int
    last_failure_reason: str | None = None


class ReliabilityReport(BaseModel):
    services: list[CircuitBreakerStatus]


class ErrorByGroup(BaseModel):
    label: str
    sample_count: int
    median_abs_pct_error: float


class BacktestReport(BaseModel):
    computed_at: datetime | None = None
    sample_count: int
    overall_median_abs_pct_error: float | None = None
    by_comp_method: list[ErrorByGroup]
    by_release_year: list[ErrorByGroup]
