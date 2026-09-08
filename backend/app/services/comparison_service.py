import httpx
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_weekly_gross_from_boxofficemojo
from app.models import Movie
from app.schemas.movie import ComparisonPoint, ComparisonSeries
from app.services.tmdb_client import tmdb_client

MAX_COMPARISON_SERIES = 6


def _to_series(movie: Movie, observations: list, is_current: bool) -> ComparisonSeries:
    return ComparisonSeries(
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        is_current=is_current,
        points=[
            ComparisonPoint(week_number=o.week_number, cumulative_gross_usd=o.cumulative_gross_usd)
            for o in observations
        ],
    )


def get_franchise_comparison(db: Session, movie: Movie) -> list[ComparisonSeries]:
    """Compare this movie's gross curve against the rest of its franchise, proactively
    ingesting the whole collection from TMDB since franchises are small and bounded."""
    if not movie.belongs_to_collection_tmdb_id:
        return []

    try:
        collection = tmdb_client.get_collection(movie.belongs_to_collection_tmdb_id)
    except httpx.HTTPStatusError:
        return []

    parts = [p for p in collection.get("parts", []) if p.get("release_date")]
    parts.sort(key=lambda p: p["release_date"])
    parts = parts[:MAX_COMPARISON_SERIES]

    series: list[ComparisonSeries] = []
    for part in parts:
        part_movie = db.query(Movie).filter(Movie.tmdb_id == part["id"]).one_or_none()
        if part_movie is None:
            try:
                part_movie = upsert_movie_from_tmdb(db, part["id"])
            except httpx.HTTPStatusError:
                continue
        if part_movie.status != "released":
            continue

        observations = ingest_weekly_gross_from_boxofficemojo(db, part_movie)
        if not observations:
            continue
        series.append(_to_series(part_movie, observations, is_current=part_movie.tmdb_id == movie.tmdb_id))

    return series


def get_same_year_comparison(db: Session, movie: Movie) -> list[ComparisonSeries]:
    """Compare against other released movies from the same calendar year that are already
    in our database (not a proactive TMDB-wide search - that's unbounded), ranked by
    worldwide gross so the most notable comps show up first."""
    if not movie.release_date:
        return []

    candidates = (
        db.query(Movie)
        .filter(
            extract("year", Movie.release_date) == movie.release_date.year,
            Movie.status == "released",
            Movie.id != movie.id,
        )
        .all()
    )
    candidates.sort(key=lambda m: m.worldwide_gross_usd or 0, reverse=True)
    candidates = candidates[: MAX_COMPARISON_SERIES - 1]

    series: list[ComparisonSeries] = []
    current_observations = ingest_weekly_gross_from_boxofficemojo(db, movie)
    if current_observations:
        series.append(_to_series(movie, current_observations, is_current=True))

    for candidate in candidates:
        observations = ingest_weekly_gross_from_boxofficemojo(db, candidate)
        if not observations:
            continue
        series.append(_to_series(candidate, observations, is_current=False))

    return series
