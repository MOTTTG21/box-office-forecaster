from datetime import date

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_weekly_gross_from_boxofficemojo
from app.models import Movie, MovieCredit, ModelRun, Person, Prediction, WeeklyGrossObservation
from app.services.tmdb_client import tmdb_client

MODEL_VERSION = "baseline-director-genre-avg-v0"
DIRECTOR_HISTORY_LIMIT = 5


def _get_or_create_model_run(db: Session) -> ModelRun:
    model_run = db.query(ModelRun).filter(ModelRun.model_version == MODEL_VERSION).one_or_none()
    if model_run is not None:
        return model_run

    model_run = ModelRun(
        model_version=MODEL_VERSION,
        model_type="baseline_heuristic",
        feature_list=["director_avg_opening_weekend", "genre_avg_opening_weekend"],
        artifact_path="n/a - heuristic, no trained artifact",
        is_active=True,
        notes=(
            "Early baseline: predicted opening weekend is the director's own historical average "
            "opening weekend (auto-backfilled from Box Office Mojo), falling back to a genre "
            "average across whatever movies are already in the database. Not a trained model yet."
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


def _director_avg_opening_weekend(db: Session, director_person_id: int, exclude_movie_id: int) -> float | None:
    result = (
        db.query(func.avg(WeeklyGrossObservation.weekend_gross_usd))
        .join(MovieCredit, MovieCredit.movie_id == WeeklyGrossObservation.movie_id)
        .filter(
            MovieCredit.person_id == director_person_id,
            MovieCredit.role == "director",
            WeeklyGrossObservation.week_number == 1,
            WeeklyGrossObservation.territory == "domestic",
            WeeklyGrossObservation.movie_id != exclude_movie_id,
        )
        .scalar()
    )
    return float(result) if result is not None else None


def _genre_avg_opening_weekend(db: Session, genres: list[str] | None, exclude_movie_id: int) -> float | None:
    if not genres:
        return None
    result = (
        db.query(func.avg(WeeklyGrossObservation.weekend_gross_usd))
        .join(Movie, Movie.id == WeeklyGrossObservation.movie_id)
        .filter(
            Movie.genres.overlap(genres),
            WeeklyGrossObservation.week_number == 1,
            WeeklyGrossObservation.territory == "domestic",
            WeeklyGrossObservation.movie_id != exclude_movie_id,
        )
        .scalar()
    )
    return float(result) if result is not None else None


def get_or_create_prediction(db: Session, movie: Movie) -> Prediction:
    model_run = _get_or_create_model_run(db)

    existing = (
        db.query(Prediction)
        .filter(Prediction.movie_id == movie.id, Prediction.model_run_id == model_run.id)
        .one_or_none()
    )
    if existing is not None:
        return existing

    director_credit = next((c for c in movie.credits if c.role == "director"), None)
    predicted = None
    if director_credit is not None:
        _backfill_director_history(db, director_credit.person, exclude_tmdb_id=movie.tmdb_id)
        predicted = _director_avg_opening_weekend(db, director_credit.person_id, exclude_movie_id=movie.id)

    if predicted is None:
        predicted = _genre_avg_opening_weekend(db, movie.genres, exclude_movie_id=movie.id)

    prediction = Prediction(
        movie_id=movie.id,
        model_run_id=model_run.id,
        predicted_opening_weekend_usd=predicted,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
