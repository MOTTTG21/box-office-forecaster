from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.limiter import STUDIO_RATE_LIMIT, limiter
from app.schemas.studio import StudioMarketComparison, StudioSlateReport
from app.services.studio_health_service import get_studio_slate_summary
from app.services.studio_market_service import get_studio_market_comparison

router = APIRouter(prefix="/api/studios", tags=["studios"])


@router.get("/slate", response_model=StudioSlateReport)
@limiter.limit(STUDIO_RATE_LIMIT)
def studio_slate(
    request: Request, year: int | None = Query(default=None), db: Session = Depends(get_db)
) -> StudioSlateReport:
    return get_studio_slate_summary(db, year or date.today().year)


@router.get("/{slug}/market-comparison", response_model=StudioMarketComparison)
@limiter.limit(STUDIO_RATE_LIMIT)
def studio_market_comparison(
    request: Request, slug: str, year: int | None = Query(default=None), db: Session = Depends(get_db)
) -> StudioMarketComparison:
    comparison = get_studio_market_comparison(db, slug, year or date.today().year)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Unknown studio")
    return comparison
