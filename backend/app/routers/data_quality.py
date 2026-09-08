from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.data_quality import DataAnomalyOut
from app.services.data_quality import refresh_data_anomalies

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


@router.get("", response_model=list[DataAnomalyOut])
def get_data_anomalies(db: Session = Depends(get_db)) -> list[DataAnomalyOut]:
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
