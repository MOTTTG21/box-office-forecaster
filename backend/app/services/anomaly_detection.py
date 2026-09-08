"""Deterministic data-quality checks against movies already in the database. Every rule flags a
concrete numeric contradiction or implausibility - never a subjective judgment call - so a flag
always cites the exact fields responsible. This module never calls an LLM; see
app/services/data_quality.py for the layer that asks Claude to explain a flag in plain English
(and only ever a flag this module already raised - it never originates a fact).
"""

import math
import statistics
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Movie, WeeklyGrossObservation

MIN_PLAUSIBLE_WIDE_RELEASE_BUDGET_USD = 50_000
MIN_THEATRICAL_RUNTIME_MINUTES = 40
MAX_PLAUSIBLE_RUNTIME_MINUTES = 240
WIDE_RELEASE_THEATER_COUNT = 600
# itself + >=5 others, so the leave-one-out stdev isn't computed from a handful of films
MIN_GENRE_SAMPLE_FOR_OUTLIER_CHECK = 6
OUTLIER_Z_SCORE_THRESHOLD = 3.0


@dataclass
class Anomaly:
    movie: Movie
    rule_name: str
    severity: str
    detail: str


def _week1(db: Session, movie: Movie) -> WeeklyGrossObservation | None:
    return (
        db.query(WeeklyGrossObservation)
        .filter(
            WeeklyGrossObservation.movie_id == movie.id,
            WeeklyGrossObservation.week_number == 1,
            WeeklyGrossObservation.territory == "domestic",
        )
        .one_or_none()
    )


def _check_domestic_exceeds_worldwide(movie: Movie) -> Anomaly | None:
    if movie.domestic_gross_usd is None or movie.worldwide_gross_usd is None:
        return None
    if movie.domestic_gross_usd <= movie.worldwide_gross_usd:
        return None
    return Anomaly(
        movie=movie,
        rule_name="domestic_exceeds_worldwide",
        severity="high",
        detail=(
            f"domestic_gross_usd=${movie.domestic_gross_usd:,} exceeds "
            f"worldwide_gross_usd=${movie.worldwide_gross_usd:,} - domestic is a subset of "
            "worldwide, so domestic can never be larger."
        ),
    )


def _check_opening_weekend_exceeds_domestic_total(
    week1: WeeklyGrossObservation | None, movie: Movie
) -> Anomaly | None:
    if week1 is None or week1.weekend_gross_usd is None or movie.domestic_gross_usd is None:
        return None
    if week1.weekend_gross_usd <= movie.domestic_gross_usd:
        return None
    return Anomaly(
        movie=movie,
        rule_name="opening_weekend_exceeds_domestic_total",
        severity="high",
        detail=(
            f"opening weekend gross of ${week1.weekend_gross_usd:,} exceeds the film's own "
            f"lifetime domestic_gross_usd=${movie.domestic_gross_usd:,} - a single weekend can't "
            "outgross the film's entire domestic run."
        ),
    )


def _check_implausible_runtime(movie: Movie) -> Anomaly | None:
    if movie.runtime_minutes is None or movie.domestic_gross_usd is None:
        return None
    if movie.runtime_minutes < MIN_THEATRICAL_RUNTIME_MINUTES:
        return Anomaly(
            movie=movie,
            rule_name="implausible_runtime",
            severity="medium",
            detail=(
                f"runtime_minutes={movie.runtime_minutes} but the film has real box office gross "
                f"on record - under {MIN_THEATRICAL_RUNTIME_MINUTES} minutes is too short for a "
                "typical theatrical feature."
            ),
        )
    if movie.runtime_minutes > MAX_PLAUSIBLE_RUNTIME_MINUTES:
        return Anomaly(
            movie=movie,
            rule_name="implausible_runtime",
            severity="low",
            detail=f"runtime_minutes={movie.runtime_minutes} is unusually long for a theatrical feature.",
        )
    return None


def _check_implausible_budget_for_wide_release(week1: WeeklyGrossObservation | None, movie: Movie) -> Anomaly | None:
    if week1 is None or week1.theater_count is None or movie.budget_usd is None:
        return None
    if week1.theater_count < WIDE_RELEASE_THEATER_COUNT:
        return None
    if movie.budget_usd >= MIN_PLAUSIBLE_WIDE_RELEASE_BUDGET_USD:
        return None
    return Anomaly(
        movie=movie,
        rule_name="implausible_budget_for_wide_release",
        severity="high",
        detail=(
            f"budget_usd=${movie.budget_usd:,} but the film opened in {week1.theater_count} "
            "theaters - a real wide release at that budget would be essentially unheard of, "
            "suggesting a data entry or unit error (e.g. thousands vs. dollars)."
        ),
    )


def _genre_budget_to_gross_outliers(movies: list[Movie]) -> list[Anomaly]:
    """Leave-one-out statistical outlier check: is this movie's worldwide-gross-to-budget ratio
    wildly out of line with other movies sharing its primary genre? Same leave-one-out discipline
    as the prediction backtest (backend/app/ml/evaluate.py) - a movie is never compared against a
    baseline that includes itself."""
    by_genre: dict[str, list[tuple[Movie, float]]] = {}
    for movie in movies:
        if not movie.genres or not movie.budget_usd or not movie.worldwide_gross_usd:
            continue
        primary_genre = movie.genres[0]
        log_ratio = math.log(movie.worldwide_gross_usd / movie.budget_usd)
        by_genre.setdefault(primary_genre, []).append((movie, log_ratio))

    anomalies: list[Anomaly] = []
    for genre, entries in by_genre.items():
        if len(entries) < MIN_GENRE_SAMPLE_FOR_OUTLIER_CHECK:
            continue
        for i, (movie, log_ratio) in enumerate(entries):
            others = [lr for j, (_, lr) in enumerate(entries) if j != i]
            mean = statistics.mean(others)
            stdev = statistics.stdev(others)
            if stdev == 0:
                continue
            z = (log_ratio - mean) / stdev
            if abs(z) < OUTLIER_Z_SCORE_THRESHOLD:
                continue
            anomalies.append(
                Anomaly(
                    movie=movie,
                    rule_name="genre_budget_to_gross_outlier",
                    severity="medium",
                    detail=(
                        f"worldwide_gross_usd/budget_usd ratio of {math.exp(log_ratio):.1f}x is "
                        f"{abs(z):.1f} standard deviations from the '{genre}' genre's typical "
                        f"{math.exp(mean):.1f}x (n={len(others)} other {genre} films, leave-one-out)."
                    ),
                )
            )
    return anomalies


def find_anomalies(db: Session) -> list[Anomaly]:
    movies = db.query(Movie).filter(Movie.status == "released").all()
    week1_by_movie_id = {movie.id: _week1(db, movie) for movie in movies}

    anomalies: list[Anomaly] = []
    for movie in movies:
        week1 = week1_by_movie_id[movie.id]
        for check in (
            _check_domestic_exceeds_worldwide(movie),
            _check_opening_weekend_exceeds_domestic_total(week1, movie),
            _check_implausible_runtime(movie),
            _check_implausible_budget_for_wide_release(week1, movie),
        ):
            if check is not None:
                anomalies.append(check)

    anomalies.extend(_genre_budget_to_gross_outliers(movies))
    return anomalies
