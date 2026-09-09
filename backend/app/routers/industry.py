from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.limiter import LOOKUP_RATE_LIMIT, limiter
from app.schemas.industry import IndustryHealthComparison
from app.services.industry_health_service import get_industry_week_over_week_comparison

router = APIRouter(prefix="/api/industry", tags=["industry"])


@router.get("/weekly-health", response_model=IndustryHealthComparison)
@limiter.limit(LOOKUP_RATE_LIMIT)
def weekly_health(request: Request, db: Session = Depends(get_db)) -> IndustryHealthComparison:
    return get_industry_week_over_week_comparison(db, date.today())
