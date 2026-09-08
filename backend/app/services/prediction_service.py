from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_weekly_gross_from_boxofficemojo
from app.models import ModelRun, Movie, MovieCredit, Person, Prediction, WeeklyGrossObservation
from app.services.tmdb_client import tmdb_client

MODEL_VERSION = "baseline-budget-scaled-v1.2"
DIRECTOR_HISTORY_LIMIT = 5
PREDICTION_REFRESH_INTERVAL = timedelta(hours=24)


def _get_or_create_model_run(db: Session) -> ModelRun:
    model_run = db.query(ModelRun).filter(ModelRun.model_version == MODEL_VERSION).one_or_none()
    if model_run is not None:
        return model_run

    model_run = ModelRun(
        model_version=MODEL_VERSION,
        model_type="baseline_heuristic",
        feature_list=["director_avg_opening_weekend_budget_scaled", "genre_avg_opening_weekend_budget_scaled"],
        artifact_path="n/a - heuristic, no trained artifact",
        is_active=True,
        notes=(
            "Baseline v1.2: predicted opening weekend comes from the director's own prior films "
            "(auto-backfilled from Box Office Mojo), or a genre average when that's unavailable. "
            "Requires BOTH this film's budget and a comp's budget to be known before using that "
            "comp - each usable comp's opening weekend is scaled by target_budget/comp_budget. "
            "No unscaled/raw fallback: 'same director' or 'same genre' doesn't guarantee similar "
            "scale (a director's career can span arthouse dramas and studio tentpoles; genre tags "
            "are broad), and blending raw dollar figures across mismatched scales produced real "
            "nonsense (a $100M+ guess for a 50-minute TV special, a ~$50K guess for a major studio "
            "sequel). No usable comps means no prediction - honest 'not enough data' over a "
            "confident wrong number. Still a heuristic, not a trained model."
        ),
    )
    db.add(model_run)
    db.commit()
    db.refresh(model_run)
    return model_run


def _backfill_director_history(db: Session, director: Person, exclude_tmdb_id: int) -> None:
    """Make sure we have this director's recent prior films (and their opening weekends) ingested."""
    try:
        credits = tmdb_client.get_person_movie_credits(director.tmdb_id)
    except httpx.HTTPStatusError:
        return

    prior_films = [
        c
        for c in credits.get("crew", [])
        if c.get("job") == "Director" and c.get("id") != exclude_tmdb_id and c.get("release_date")
    ]
    prior_films.sort(key=lambda c: c["release_date"], reverse=True)

    for film in prior_films[:DIRECTOR_HISTORY_LIMIT]:
        movie = db.query(Movie).filter(Movie.tmdb_id == film["id"]).one_or_none()
        if movie is None:
            try:
                movie = upsert_movie_from_tmdb(db, film["id"])
            except httpx.HTTPStatusError:
                continue
        if movie.status == "released":
            ingest_weekly_gross_from_boxofficemojo(db, movie)


def _budget_scaled_average(rows: list[tuple[int | None, int | None]], target_budget_usd: int | None) -> float | None:
    """Average opening weekends across comps, scaling each by target_budget/comp_budget - only when
    BOTH budgets are known. A "same director" or "same genre" comp is no guarantee of similar scale
    (a director's career can span arthouse dramas and studio franchise films; a genre tag is broad),
    so an unscaled comp is dropped rather than blended in raw. This produced real nonsense before:
    a director whose only real comp was a Netflix original's token theatrical run predicted a
    Sandra Bullock/Nicole Kidman franchise sequel's opening at ~$50K. No usable comps means no
    prediction - honest "not enough data" beats a confident wrong number."""
    estimates = [
        weekend_gross_usd * (target_budget_usd / comp_budget_usd)
        for weekend_gross_usd, comp_budget_usd in rows
        if weekend_gross_usd is not None and target_budget_usd and comp_budget_usd
    ]
    return sum(estimates) / len(estimates) if estimates else None


def _director_opening_weekend(
    db: Session, director_person_id: int, exclude_movie_id: int, target_budget_usd: int | None
) -> float | None:
    if not target_budget_usd:
        return None
    rows = (
        db.query(WeeklyGrossObservation.weekend_gross_usd, Movie.budget_usd)
        .join(MovieCredit, MovieCredit.movie_id == WeeklyGrossObservation.movie_id)
        .join(Movie, Movie.id == WeeklyGrossObservation.movie_id)
        .filter(
            MovieCredit.person_id == director_person_id,
            MovieCredit.role == "director",
            WeeklyGrossObservation.week_number == 1,
            WeeklyGrossObservation.territory == "domestic",
            WeeklyGrossObservation.movie_id != exclude_movie_id,
        )
        .all()
    )
    return _budget_scaled_average(rows, target_budget_usd)


def _genre_opening_weekend(
    db: Session, genres: list[str] | None, exclude_movie_id: int, target_budget_usd: int | None
) -> float | None:
    if not genres:
        return None
    if not target_budget_usd:
        # short-circuit: _budget_scaled_average would return None anyway without a target
        # budget to scale against, so skip the query entirely
        return None
    rows = (
        db.query(WeeklyGrossObservation.weekend_gross_usd, Movie.budget_usd)
        .join(Movie, Movie.id == WeeklyGrossObservation.movie_id)
        .filter(
            Movie.genres.overlap(genres),
            WeeklyGrossObservation.week_number == 1,
            WeeklyGrossObservation.territory == "domestic",
            WeeklyGrossObservation.movie_id != exclude_movie_id,
        )
        .all()
    )
    return _budget_scaled_average(rows, target_budget_usd)


def _compute_predicted_opening_weekend(db: Session, movie: Movie) -> float | None:
    director_credit = next((c for c in movie.credits if c.role == "director"), None)
    predicted = None
    if director_credit is not None:
        _backfill_director_history(db, director_credit.person, exclude_tmdb_id=movie.tmdb_id)
        predicted = _director_opening_weekend(
            db, director_credit.person_id, exclude_movie_id=movie.id, target_budget_usd=movie.budget_usd
        )

    if predicted is None:
        predicted = _genre_opening_weekend(
            db, movie.genres, exclude_movie_id=movie.id, target_budget_usd=movie.budget_usd
        )

    return predicted


def get_or_create_prediction(db: Session, movie: Movie) -> Prediction:
    """Predictions refresh once a day rather than caching forever - e.g. a budget figure that
    gets added to TMDB, or a new comp getting ingested, should show up in tomorrow's prediction
    without waiting on a new model version."""
    model_run = _get_or_create_model_run(db)

    existing = (
        db.query(Prediction)
        .filter(Prediction.movie_id == movie.id, Prediction.model_run_id == model_run.id)
        .one_or_none()
    )
    is_stale = existing is not None and (
        datetime.now(timezone.utc) - existing.predicted_at
    ) > PREDICTION_REFRESH_INTERVAL
    if existing is not None and not is_stale:
        return existing

    predicted = _compute_predicted_opening_weekend(db, movie)

    if existing is not None:
        existing.predicted_opening_weekend_usd = predicted
        existing.predicted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    prediction = Prediction(
        movie_id=movie.id,
        model_run_id=model_run.id,
        predicted_opening_weekend_usd=predicted,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
