"""Backtest the holdover decline model (decline_model.py) leave-one-out: for every real
week-over-week transition already in the database, predict that week's gross from the prior
week's actual gross and the OTHER movies' ratio at that same week (this movie's own transition
excluded from the ratio pool), then compare to what actually happened.

Genre-splitting the ratio pool was tried and rejected here - at every sample-size threshold
tested it came out identical to or worse than the plain, ungrouped ratio, so the shipped model
in decline_model.py doesn't use it. This file keeps that comparison so the decision stays
checkable, the same "test before shipping" discipline used for the opening-weekend model's
theater-count experiment.

Run with: python -m app.ml.evaluate_decline
"""

import statistics

from app.core.db import SessionLocal
from app.ml.decline_model import Transition, load_transitions_from_db, predict_next_weekend_gross

# beyond this, sample size per week gets thin and it's outside what a "top 10 in theaters"
# list would ever need
MAX_WEEK_FOR_REPORT = 12


def _backtest(transitions: list[Transition]) -> list[dict]:
    results = []
    for t in transitions:
        if t.week_number > MAX_WEEK_FOR_REPORT:
            continue
        predicted = predict_next_weekend_gross(
            transitions, exclude_movie_id=t.movie_id, target_week=t.week_number, prior_weekend_gross=t.prior_gross
        )
        pct_error = ((predicted - t.actual_gross) / t.actual_gross * 100) if predicted is not None else None
        results.append(
            {
                "week_number": t.week_number,
                "actual": t.actual_gross,
                "predicted": predicted,
                "pct_error": pct_error,
            }
        )
    return results


def _report(label: str, results: list[dict]) -> None:
    covered = [r for r in results if r["predicted"] is not None]
    errors = [abs(r["pct_error"]) for r in covered]
    print(f"\n{label}")
    print(f"  transitions: {len(results)}  covered: {len(covered)}")
    if errors:
        print(f"  median abs % error: {statistics.median(errors):.0f}%")
        print(f"  mean abs % error:   {statistics.mean(errors):.0f}%")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        transitions = load_transitions_from_db(session)
        in_range = [t for t in transitions if t.week_number <= MAX_WEEK_FOR_REPORT]
        print(f"Total transitions available (through week {MAX_WEEK_FOR_REPORT}): {len(in_range)}")

        _report("Decline model (leave-one-out, ungrouped)", _backtest(transitions))

        naive_errors = [abs((t.prior_gross - t.actual_gross) / t.actual_gross * 100) for t in in_range]
        print('\nNaive baseline ("assume no change from last week")')
        print(f"  median abs % error: {statistics.median(naive_errors):.0f}%")
        print(f"  mean abs % error:   {statistics.mean(naive_errors):.0f}%")
    finally:
        session.close()
