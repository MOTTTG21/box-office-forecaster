"""Records one prediction snapshot per (movie, week being predicted) per calendar day, so
there's an honest day-by-day history behind the fluctuating forecast chart. Once a day's
snapshot is recorded it's never silently overwritten by a later recomputation that same day -
so the number shown in the live Top 10 list for "today" always matches the point charted for
today, and the history reflects what was actually believed on each day, not a revised-after-
the-fact value.
"""

from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from app.models import PredictionSnapshot


def get_or_record_snapshot(
    db: Session,
    movie_id: int,
    week_number: int,
    is_new_release: bool,
    compute_prediction: Callable[[], float | None],
) -> float | None:
    """Returns today's snapshot for (movie_id, week_number) if one already exists; otherwise
    computes it via `compute_prediction` (only called when needed - it's the expensive path),
    records it, and returns that value."""
    today = date.today()
    existing = (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.movie_id == movie_id,
            PredictionSnapshot.week_number == week_number,
            PredictionSnapshot.snapshot_date == today,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing.predicted_weekend_gross_usd

    predicted = compute_prediction()
    db.add(
        PredictionSnapshot(
            movie_id=movie_id,
            week_number=week_number,
            snapshot_date=today,
            is_new_release=is_new_release,
            predicted_weekend_gross_usd=predicted,
        )
    )
    db.commit()
    return predicted


def get_latest_tracked_week(db: Session, movie_id: int) -> int | None:
    """The most recent week_number this movie has any snapshot history for - the "currently
    active" forecast to chart, since a movie can be tracked for one week, drop out of the top
    10, then re-enter and be tracked again for a later week."""
    latest = (
        db.query(PredictionSnapshot)
        .filter(PredictionSnapshot.movie_id == movie_id)
        .order_by(PredictionSnapshot.week_number.desc())
        .first()
    )
    return latest.week_number if latest else None


def get_snapshot_history(db: Session, movie_id: int, week_number: int) -> list[PredictionSnapshot]:
    return (
        db.query(PredictionSnapshot)
        .filter(PredictionSnapshot.movie_id == movie_id, PredictionSnapshot.week_number == week_number)
        .order_by(PredictionSnapshot.snapshot_date)
        .all()
    )
