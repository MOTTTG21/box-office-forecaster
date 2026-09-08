"""Predicts a holdover movie's upcoming weekend gross from its own most recent weekend gross,
scaled by an expected week-over-week decline ratio - the same modeling approach as the opening-
weekend heuristic (average historical comps, leave-one-out), just comparing a movie's own
trajectory against other movies' at the same week-in-release instead of comparing budgets.

A genre-specific decline ratio was tested and rejected (see backend/app/ml/evaluate_decline.py):
splitting by genre never beat the plain, ungrouped ratio for that week number, at any sample-size
threshold tried - the dataset just isn't large enough yet for a genre split to add anything over
noise. Backtested result: 23% median absolute error vs. 73% for a naive "assume no change from
last week" baseline.
"""

import statistics
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import WeeklyGrossObservation


@dataclass
class Transition:
    movie_id: int
    week_number: int
    prior_gross: int
    actual_gross: int

    @property
    def ratio(self) -> float:
        return self.actual_gross / self.prior_gross


def collect_transitions(observations_by_movie: dict[int, list[WeeklyGrossObservation]]) -> list[Transition]:
    transitions: list[Transition] = []
    for movie_id, observations in observations_by_movie.items():
        by_week = {o.week_number: o for o in observations}
        for week_number, obs in by_week.items():
            prior = by_week.get(week_number - 1)
            if prior is None or not prior.weekend_gross_usd or not obs.weekend_gross_usd:
                continue
            transitions.append(
                Transition(
                    movie_id=movie_id,
                    week_number=week_number,
                    prior_gross=prior.weekend_gross_usd,
                    actual_gross=obs.weekend_gross_usd,
                )
            )
    return transitions


def load_transitions_from_db(db: Session) -> list[Transition]:
    """Load every real week-over-week transition currently in the database. Called once per
    request (not once per movie) - the resulting list is cheap to filter in memory per movie."""
    observations = (
        db.query(WeeklyGrossObservation)
        .filter(
            WeeklyGrossObservation.territory == "domestic",
            WeeklyGrossObservation.source == "boxofficemojo_scrape",
        )
        .all()
    )
    by_movie: dict[int, list[WeeklyGrossObservation]] = {}
    for obs in observations:
        by_movie.setdefault(obs.movie_id, []).append(obs)
    return collect_transitions(by_movie)


def _leave_one_out_ratios(transitions: list[Transition], exclude_movie_id: int, target_week: int) -> list[float]:
    return [t.ratio for t in transitions if t.week_number == target_week and t.movie_id != exclude_movie_id]


def predict_next_weekend_gross(
    transitions: list[Transition],
    exclude_movie_id: int,
    target_week: int,
    prior_weekend_gross: int,
) -> float | None:
    ratios = _leave_one_out_ratios(transitions, exclude_movie_id, target_week)
    if not ratios:
        return None
    return prior_weekend_gross * statistics.median(ratios)
