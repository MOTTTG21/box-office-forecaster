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
Pass --save to also replace the cached backtest_predictions table (see app/models/
backtest_prediction.py for why this is a batch step rather than a live endpoint) - that table is
what GET /api/data-quality/backtest reads to show a live error-over-time breakdown without
re-running this script's TMDB calls on every page view.
"""

import statistics
import sys

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import BacktestPrediction, Movie, WeeklyGrossObservation
from app.services.prediction_service import _compute_predicted_opening_weekend_with_method

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

        predicted, method = _compute_predicted_opening_weekend_with_method(db, movie)
        actual = week1.weekend_gross_usd
        pct_error = ((predicted - actual) / actual * 100) if predicted is not None else None

        results.append(
            {
                "title": movie.title,
                "release_year": movie.release_date.year if movie.release_date else None,
                "budget_usd": movie.budget_usd,
                "actual": actual,
                "predicted": predicted,
                "pct_error": pct_error,
                "comp_method": method,
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


def save_results(db: Session, results: list[dict]) -> None:
    """Replaces the whole cached table - this reports the model as it stands today, not a
    history of past runs, so stale rows from a previous run must not linger alongside fresh
    ones."""
    covered = [r for r in results if r["predicted"] is not None]
    db.query(BacktestPrediction).delete()
    db.add_all(
        BacktestPrediction(
            title=r["title"],
            release_year=r["release_year"],
            budget_usd=r["budget_usd"],
            actual_opening_weekend_usd=r["actual"],
            predicted_opening_weekend_usd=r["predicted"],
            pct_error=r["pct_error"],
            comp_method=r["comp_method"],
        )
        for r in covered
    )
    db.commit()
    print(f"\nSaved {len(covered)} backtest rows to backtest_predictions.")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        backtest_results = backtest(session)
        print_report(backtest_results)
        if "--save" in sys.argv:
            save_results(session, backtest_results)
    finally:
        session.close()
