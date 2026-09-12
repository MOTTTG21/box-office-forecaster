from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.limiter import DATA_QUALITY_RATE_LIMIT, limiter
from app.schemas.data_quality import (
    BacktestReport,
    CircuitBreakerStatus,
    DataAnomalyOut,
    LatencyReport,
    ReliabilityReport,
)
from app.services.backtest_report_service import get_backtest_report
from app.services.circuit_breaker import all_breaker_snapshots
from app.services.data_quality import refresh_data_anomalies
from app.services.latency_service import get_latency_report

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


@router.get("/latency", response_model=LatencyReport)
@limiter.limit(DATA_QUALITY_RATE_LIMIT)
def get_latency(request: Request, db: Session = Depends(get_db)) -> LatencyReport:
    return get_latency_report(db)


@router.get("/reliability", response_model=ReliabilityReport)
@limiter.limit(DATA_QUALITY_RATE_LIMIT)
def get_reliability(request: Request) -> ReliabilityReport:
    return ReliabilityReport(
        services=[CircuitBreakerStatus(**snapshot) for snapshot in all_breaker_snapshots()]
    )


@router.get("/backtest", response_model=BacktestReport)
@limiter.limit(DATA_QUALITY_RATE_LIMIT)
def get_backtest(request: Request, db: Session = Depends(get_db)) -> BacktestReport:
    return get_backtest_report(db)


@router.get("", response_model=list[DataAnomalyOut])
@limiter.limit(DATA_QUALITY_RATE_LIMIT)
def get_data_anomalies(request: Request, db: Session = Depends(get_db)) -> list[DataAnomalyOut]:
    rows = refresh_data_anomalies(db)
    rows.sort(key=lambda r: (SEVERITY_RANK.get(r.severity, 99), r.movie.title))
    return [
        DataAnomalyOut(
            tmdb_id=row.movie.tmdb_id,
            title=row.movie.title,
            poster_path=row.movie.poster_path,
            rule_name=row.rule_name,
            severity=row.severity,
            detail=row.detail,
            ai_explanation=row.ai_explanation,
            detected_at=row.detected_at,
        )
        for row in rows
    ]
