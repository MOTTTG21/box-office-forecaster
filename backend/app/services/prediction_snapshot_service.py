"""Records one prediction snapshot per (movie, week being predicted) per calendar day, so
there's an honest day-by-day history behind the fluctuating forecast chart. Once a day's
snapshot is recorded it's never silently overwritten by a later recomputation that same day -
so the number shown in the live Top 10 list for "today" always matches the point charted for
today, and the history reflects what was actually believed on each day, not a revised-after-
the-fact value.
"""

from collections.abc import Callable
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import PredictionSnapshot


def _existing_snapshot(db: Session, movie_id: int, week_number: int, today: date) -> PredictionSnapshot | None:
    return (
        db.query(PredictionSnapshot)
        .filter(
            PredictionSnapshot.movie_id == movie_id,
            PredictionSnapshot.week_number == week_number,
            PredictionSnapshot.snapshot_date == today,
        )
        .one_or_none()
    )


def get_or_record_snapshot(
    db: Session,
    movie_id: int,
    week_number: int,
    is_new_release: bool,
    compute_prediction: Callable[[], tuple[float | None, str | None]],
) -> float | None:
    """Returns today's snapshot for (movie_id, week_number) if one already exists; otherwise
    computes it via `compute_prediction` (only called when needed - it's the expensive path,
    which may include a live news-research call), records it, and returns the predicted value.
    `compute_prediction` returns (predicted_value, news_reason) - the reason is stored but not
    returned here; read it back via get_snapshot_history for the chart.

    Two concurrent requests can both see "no snapshot yet" and both compute + try to insert -
    the second one to commit hits the unique constraint on (movie_id, week_number,
    snapshot_date). Rather than 500 (which happened in production the first time this occurred),
    treat that as a signal the other request already won: roll back the failed insert and
    return the row it just committed instead of the value this request computed."""
    today = date.today()
    existing = _existing_snapshot(db, movie_id, week_number, today)
    if existing is not None:
        return existing.predicted_weekend_gross_usd

    predicted, reason = compute_prediction()
    db.add(
        PredictionSnapshot(
            movie_id=movie_id,
            week_number=week_number,
            snapshot_date=today,
            is_new_release=is_new_release,
            predicted_weekend_gross_usd=predicted,
            news_reason=reason,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        winner = _existing_snapshot(db, movie_id, week_number, today)
        return winner.predicted_weekend_gross_usd if winner else predicted
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
