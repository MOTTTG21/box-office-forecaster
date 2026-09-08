from fastapi import APIRouter

from app.core.limiter import limiter

router = APIRouter(tags=["health"])


@router.get("/api/health")
@limiter.exempt
def health_check() -> dict[str, str]:
    return {"status": "ok"}
