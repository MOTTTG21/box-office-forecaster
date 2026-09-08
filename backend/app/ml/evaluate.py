"""Backtest the baseline prediction heuristic against movies we already have real opening-weekend
actuals for. For each eligible movie, predicts its opening weekend leave-one-out (excluding itself
from its own comp pool, same as at request time) and compares to the real result.

Eligibility is restricted to movies that themselves opened wide (>= MIN_WIDE_RELEASE_THEATERS
theaters) - that's the population "This Week" actually predicts for. Without this filter, the
backtest set also included small indie/arthouse films that only entered the database via a
director's auto-backfilled history, and no comp-selection logic can fix a limited-release film's
prediction anyway: it was never going to open like a wide release regardless of budget. Including
them didn't make the model look more honest, it just diluted a measurement that's supposed to
answer "how good is this for what it's actually used for" with an unrelated, unsolvable case.

Run with: python -m app.ml.evaluate
"""

import statistics

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import Movie, WeeklyGrossObservation
from app.services.prediction_service import _compute_predicted_opening_weekend

MIN_WIDE_RELEASE_THEATERS = 600


def backtest(db: Session) -> list[dict]:
    movies = db.query(Movie).filter(Movie.budget_usd.isnot(None), Movie.status == "released").all()

    results = []
    for movie in movies:
        week1 = (
            db.query(WeeklyGrossObservation)
            .filter(
                WeeklyGrossObservation.movie_id == movie.id,
                WeeklyGrossObservation.week_number == 1,
                WeeklyGrossObservation.territory == "domestic",
            )
            .one_or_none()
        )
        if week1 is None or week1.weekend_gross_usd is None:
            continue
        if not week1.theater_count or week1.theater_count < MIN_WIDE_RELEASE_THEATERS:
            continue  # not a wide release - not the population this model is used for

        predicted = _compute_predicted_opening_weekend(db, movie)
        actual = week1.weekend_gross_usd
        pct_error = ((predicted - actual) / actual * 100) if predicted is not None else None

        results.append(
            {
                "title": movie.title,
                "budget_usd": movie.budget_usd,
                "actual": actual,
                "predicted": predicted,
                "pct_error": pct_error,
            }
        )

    return results


def print_report(results: list[dict]) -> None:
    covered = [r for r in results if r["predicted"] is not None]
    print(f"Eligible movies (wide release, budget known, real opening actual on record): {len(results)}")
    if not results:
        print("Nothing to backtest yet.")
        return
    print(f"Predictions produced: {len(covered)} ({len(covered) / len(results) * 100:.0f}% coverage)")
    print()
    for r in sorted(results, key=lambda r: r["title"]):
        pred_str = f"${r['predicted']:,.0f}" if r["predicted"] is not None else "no prediction"
        err_str = f"{r['pct_error']:+.0f}%" if r["pct_error"] is not None else "n/a"
        print(f"{r['title']:42s} actual=${r['actual']:>13,d}  predicted={pred_str:>16s}  error={err_str}")

    if covered:
        errors = [abs(r["pct_error"]) for r in covered]
        print()
        print(f"Median absolute % error: {statistics.median(errors):.0f}%")
        print(f"Mean absolute % error:   {statistics.mean(errors):.0f}%")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        print_report(backtest(session))
    finally:
        session.close()
