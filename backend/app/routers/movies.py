import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_weekly_gross_from_boxofficemojo
from app.models import Movie
from app.schemas.movie import MovieBrowseRows, MovieDetail, MovieSearchResult, PersonOut, WeeklyGrossPoint
from app.services.tmdb_client import tmdb_client

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


@router.get("/{tmdb_id}", response_model=MovieDetail)
def get_movie(tmdb_id: int, db: Session = Depends(get_db)) -> MovieDetail:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail="Movie not found")

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
