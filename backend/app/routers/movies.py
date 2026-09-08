from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_lifetime_grosses, ingest_weekly_gross_from_boxofficemojo
from app.models import Movie
from app.schemas.movie import (
    ComparisonSeries,
    MovieBrowseRows,
    MovieDetail,
    MovieSearchResult,
    PersonOut,
    ThisWeekMovie,
    WeeklyGrossPoint,
)
from app.services.comparison_service import get_franchise_comparison, get_same_year_comparison
from app.services.prediction_service import get_or_create_prediction
from app.services.profitability import compute_profitability_status
from app.services.tmdb_client import tmdb_client

THIS_WEEK_LOOKAHEAD_DAYS = 14
THIS_WEEK_LOOKBACK_DAYS = 6
THIS_WEEK_MAX_RESULTS = 10

router = APIRouter(prefix="/api/movies", tags=["movies"])

BROWSE_ROW_PATHS = {
    "trending": "/trending/movie/week",
    "popular": "/movie/popular",
    "top_rated": "/movie/top_rated",
    "upcoming": "/movie/upcoming",
}


def _to_search_results(results: list[dict]) -> list[MovieSearchResult]:
    return [
        MovieSearchResult(
            tmdb_id=result["id"],
            title=result["title"],
            release_date=result.get("release_date") or None,
            poster_path=result.get("poster_path"),
        )
        for result in results
    ]


@router.get("/search", response_model=list[MovieSearchResult])
def search_movies(q: str) -> list[MovieSearchResult]:
    return _to_search_results(tmdb_client.search_movies(q))


@router.get("/browse", response_model=MovieBrowseRows)
def browse_movies() -> MovieBrowseRows:
    return MovieBrowseRows(
        **{row: _to_search_results(tmdb_client.get_movie_list(path)) for row, path in BROWSE_ROW_PATHS.items()}
    )


@router.get("/this-week", response_model=list[ThisWeekMovie])
def this_week_movies(db: Session = Depends(get_db)) -> list[ThisWeekMovie]:
    today = date.today()
    window_start = today - timedelta(days=THIS_WEEK_LOOKBACK_DAYS)
    window_end = today + timedelta(days=THIS_WEEK_LOOKAHEAD_DAYS)

    candidates = tmdb_client.discover_movies_by_date_range(window_start.isoformat(), window_end.isoformat())

    in_window = []
    for result in candidates:
        release_date_str = result.get("release_date")
        if not release_date_str:
            continue
        release_date = date.fromisoformat(release_date_str)
        if window_start <= release_date <= window_end:
            in_window.append(result)
    in_window = in_window[:THIS_WEEK_MAX_RESULTS]

    output: list[ThisWeekMovie] = []
    for result in in_window:
        movie = db.query(Movie).filter(Movie.tmdb_id == result["id"]).one_or_none()
        if movie is None:
            try:
                movie = upsert_movie_from_tmdb(db, result["id"])
            except httpx.HTTPStatusError:
                continue

        prediction = get_or_create_prediction(db, movie)

        actual_opening = None
        if movie.release_date and movie.release_date <= today:
            observations = ingest_weekly_gross_from_boxofficemojo(db, movie)
            opening = next((o for o in observations if o.week_number == 1), None)
            if opening:
                actual_opening = opening.weekend_gross_usd

        output.append(
            ThisWeekMovie(
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                release_date=movie.release_date,
                poster_path=movie.poster_path,
                predicted_opening_weekend_usd=prediction.predicted_opening_weekend_usd,
                actual_opening_weekend_usd=actual_opening,
            )
        )

    output.sort(key=lambda m: m.release_date or date.max)
    return output


@router.get("/{tmdb_id}", response_model=MovieDetail)
def get_movie(tmdb_id: int, db: Session = Depends(get_db)) -> MovieDetail:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail="Movie not found")

    if movie.status == "released":
        movie = ingest_lifetime_grosses(db, movie)

    director = next((c for c in movie.credits if c.role == "director"), None)
    cast = sorted(
        (c for c in movie.credits if c.role == "actor"),
        key=lambda c: c.cast_order if c.cast_order is not None else 999,
    )

    return MovieDetail(
        id=movie.id,
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        overview=movie.overview,
        release_date=movie.release_date,
        status=movie.status,
        runtime_minutes=movie.runtime_minutes,
        budget_usd=movie.budget_usd,
        domestic_gross_usd=movie.domestic_gross_usd,
        worldwide_gross_usd=movie.worldwide_gross_usd,
        profitability_status=compute_profitability_status(movie.budget_usd, movie.worldwide_gross_usd),
        genres=movie.genres,
        poster_path=movie.poster_path,
        popularity_tmdb_snapshot=movie.popularity_tmdb_snapshot,
        director=PersonOut.model_validate(director.person) if director else None,
        cast=[
            PersonOut(
                id=c.person.id,
                tmdb_id=c.person.tmdb_id,
                name=c.person.name,
                character_name=c.character_name,
            )
            for c in cast
        ],
    )


@router.get("/{tmdb_id}/weekly-gross", response_model=list[WeeklyGrossPoint])
def get_weekly_gross(tmdb_id: int, db: Session = Depends(get_db)) -> list[WeeklyGrossPoint]:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail="Movie not found")

    observations = ingest_weekly_gross_from_boxofficemojo(db, movie)
    return [WeeklyGrossPoint.model_validate(obs) for obs in observations]


@router.get("/{tmdb_id}/compare/franchise", response_model=list[ComparisonSeries])
def compare_franchise(tmdb_id: int, db: Session = Depends(get_db)) -> list[ComparisonSeries]:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail="Movie not found")

    return get_franchise_comparison(db, movie)


@router.get("/{tmdb_id}/compare/year", response_model=list[ComparisonSeries])
def compare_year(tmdb_id: int, db: Session = Depends(get_db)) -> list[ComparisonSeries]:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail="Movie not found")

    return get_same_year_comparison(db, movie)
