from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.limiter import DEFAULT_RATE_LIMIT, LOOKUP_RATE_LIMIT, SEARCH_RATE_LIMIT, limiter
from app.etl.ingest_omdb import ingest_critic_scores
from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_lifetime_grosses, ingest_weekly_gross_from_boxofficemojo
from app.ml.decline_model import load_transitions_from_db, predict_next_weekend_gross
from app.models import Movie, WeeklyGrossObservation
from app.schemas.movie import (
    ComparisonSeries,
    MovieBrowseRows,
    MovieDetail,
    MovieSearchResult,
    PersonOut,
    PredictionHistory,
    PredictionSnapshotPoint,
    ThisWeekMovie,
    WeeklyGrossPoint,
)
from app.services.comparison_service import get_franchise_comparison, get_same_year_comparison
from app.services.inflation import LATEST_CPI_YEAR, adjust_for_inflation
from app.services.news_signal_service import apply_news_adjustment
from app.services.prediction_service import get_or_create_prediction
from app.services.prediction_snapshot_service import (
    get_latest_tracked_week,
    get_or_record_snapshot,
    get_snapshot_history,
)
from app.services.profitability import compute_profitability_status
from app.services.tmdb_client import tmdb_client

TOP_IN_THEATERS_LIMIT = 10
MIN_THEATRICAL_RUNTIME_MINUTES = 60

router = APIRouter(prefix="/api/movies", tags=["movies"])


def _current_box_office_week(today: date) -> tuple[date, date]:
    """The box office week is Monday-Sunday (studios report official weekend numbers Sunday)."""
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

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
@limiter.limit(SEARCH_RATE_LIMIT)
def search_movies(request: Request, q: str = Query(..., max_length=200)) -> list[MovieSearchResult]:
    return _to_search_results(tmdb_client.search_movies(q))


@router.get("/browse", response_model=MovieBrowseRows)
@limiter.limit(DEFAULT_RATE_LIMIT)
def browse_movies(request: Request) -> MovieBrowseRows:
    return MovieBrowseRows(
        **{row: _to_search_results(tmdb_client.get_movie_list(path)) for row, path in BROWSE_ROW_PATHS.items()}
    )


def _is_real_theatrical_release(movie: Movie) -> bool:
    # TMDB's release-type filter still lets through TV specials that got a token
    # theatrical qualifying run (e.g. a 50-minute streaming special) - these aren't
    # real wide releases and have no meaningful box office trajectory to predict.
    return movie.runtime_minutes is None or movie.runtime_minutes >= MIN_THEATRICAL_RUNTIME_MINUTES


def _new_release_entries(db: Session, today: date, window_start: date, window_end: date) -> list[ThisWeekMovie]:
    candidates = tmdb_client.discover_movies_by_date_range(window_start.isoformat(), window_end.isoformat())

    entries: list[ThisWeekMovie] = []
    for result in candidates:
        release_date_str = result.get("release_date")
        if not release_date_str:
            continue
        release_date = date.fromisoformat(release_date_str)
        if not (window_start <= release_date <= window_end):
            continue

        movie = db.query(Movie).filter(Movie.tmdb_id == result["id"]).one_or_none()
        if movie is None:
            try:
                movie = upsert_movie_from_tmdb(db, result["id"])
            except httpx.HTTPStatusError:
                continue

        if not _is_real_theatrical_release(movie):
            continue

        prediction = get_or_create_prediction(db, movie)
        predicted = get_or_record_snapshot(
            db,
            movie_id=movie.id,
            week_number=1,
            is_new_release=True,
            compute_prediction=lambda p=prediction, m=movie: apply_news_adjustment(
                p.predicted_opening_weekend_usd, m.title
            ),
        )

        actual = None
        if movie.release_date and movie.release_date <= today:
            observations = ingest_weekly_gross_from_boxofficemojo(db, movie)
            opening = next((o for o in observations if o.week_number == 1), None)
            if opening:
                actual = opening.weekend_gross_usd

        entries.append(
            ThisWeekMovie(
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                release_date=movie.release_date,
                poster_path=movie.poster_path,
                is_new_release=True,
                week_number=1,
                predicted_weekend_gross_usd=predicted,
                actual_weekend_gross_usd=actual,
                previous_weekend_gross_usd=None,
            )
        )
    return entries


def _holdover_entries(db: Session, exclude_tmdb_ids: set[int]) -> list[ThisWeekMovie]:
    now_playing = tmdb_client.get_movie_list("/movie/now_playing")
    transitions = load_transitions_from_db(db)

    entries: list[ThisWeekMovie] = []
    for result in now_playing:
        if result["id"] in exclude_tmdb_ids:
            continue

        movie = db.query(Movie).filter(Movie.tmdb_id == result["id"]).one_or_none()
        if movie is None:
            try:
                movie = upsert_movie_from_tmdb(db, result["id"])
            except httpx.HTTPStatusError:
                continue

        if movie.status != "released" or not _is_real_theatrical_release(movie):
            continue

        observations = ingest_weekly_gross_from_boxofficemojo(db, movie)
        if not observations:
            continue
        latest = max(observations, key=lambda o: o.week_number)
        if latest.weekend_gross_usd is None:
            continue

        target_week = latest.week_number + 1

        def _compute_holdover_prediction(m=movie, tw=target_week, pg=latest.weekend_gross_usd):
            base = predict_next_weekend_gross(
                transitions, exclude_movie_id=m.id, target_week=tw, prior_weekend_gross=pg
            )
            return apply_news_adjustment(base, m.title)

        predicted = get_or_record_snapshot(
            db,
            movie_id=movie.id,
            week_number=target_week,
            is_new_release=False,
            compute_prediction=_compute_holdover_prediction,
        )
        # in case this weekend's real number has already landed by the time this runs
        actual_row = next((o for o in observations if o.week_number == target_week), None)

        entries.append(
            ThisWeekMovie(
                tmdb_id=movie.tmdb_id,
                title=movie.title,
                release_date=movie.release_date,
                poster_path=movie.poster_path,
                is_new_release=False,
                week_number=target_week,
                predicted_weekend_gross_usd=predicted,
                actual_weekend_gross_usd=actual_row.weekend_gross_usd if actual_row else None,
                previous_weekend_gross_usd=latest.weekend_gross_usd,
            )
        )
    return entries


@router.get("/this-week", response_model=list[ThisWeekMovie])
@limiter.limit(LOOKUP_RATE_LIMIT)
def this_week_movies(request: Request, db: Session = Depends(get_db)) -> list[ThisWeekMovie]:
    """The top 10 highest-grossing films predicted for the current box office weekend - new
    releases (opening-weekend heuristic) and holdovers (leave-one-out decline model, see
    backend/app/ml/decline_model.py) ranked together by predicted gross, not just new releases."""
    today = date.today()
    window_start, window_end = _current_box_office_week(today)

    new_releases = _new_release_entries(db, today, window_start, window_end)
    holdovers = _holdover_entries(db, exclude_tmdb_ids={e.tmdb_id for e in new_releases})

    combined = new_releases + holdovers
    combined.sort(key=lambda e: e.actual_weekend_gross_usd or e.predicted_weekend_gross_usd or 0, reverse=True)
    return combined[:TOP_IN_THEATERS_LIMIT]


@router.get("/{tmdb_id}/prediction-history", response_model=PredictionHistory | None)
@limiter.limit(LOOKUP_RATE_LIMIT)
def get_prediction_history(request: Request, tmdb_id: int, db: Session = Depends(get_db)) -> PredictionHistory | None:
    """The day-by-day snapshot history for whichever week this movie is currently (or was most
    recently) being tracked for, plus the real actual once it's known - the fluctuating forecast
    chart's data source. None if this movie has never been tracked in the Top 10 list."""
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        return None

    week_number = get_latest_tracked_week(db, movie.id)
    if week_number is None:
        return None

    snapshots = get_snapshot_history(db, movie.id, week_number)
    is_new_release = snapshots[0].is_new_release if snapshots else True

    actual_row = (
        db.query(WeeklyGrossObservation)
        .filter(
            WeeklyGrossObservation.movie_id == movie.id,
            WeeklyGrossObservation.week_number == week_number,
            WeeklyGrossObservation.territory == "domestic",
        )
        .one_or_none()
    )

    return PredictionHistory(
        week_number=week_number,
        is_new_release=is_new_release,
        snapshots=[
            PredictionSnapshotPoint(
                snapshot_date=s.snapshot_date,
                predicted_weekend_gross_usd=s.predicted_weekend_gross_usd,
                news_reason=s.news_reason,
            )
            for s in snapshots
        ],
        actual_weekend_gross_usd=actual_row.weekend_gross_usd if actual_row else None,
    )


@router.get("/{tmdb_id}", response_model=MovieDetail)
@limiter.limit(LOOKUP_RATE_LIMIT)
def get_movie(request: Request, tmdb_id: int, db: Session = Depends(get_db)) -> MovieDetail:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=404, detail="Movie not found") from exc

    if movie.status == "released":
        movie = ingest_lifetime_grosses(db, movie)
    movie = ingest_critic_scores(db, movie)

    director = next((c for c in movie.credits if c.role == "director"), None)
    cast = sorted(
        (c for c in movie.credits if c.role == "actor"),
        key=lambda c: c.cast_order if c.cast_order is not None else 999,
    )

    # Only worth showing "in today's dollars" for a film that wasn't released this calendar
    # year - a current-year release's raw figures already are today's dollars.
    release_year = movie.release_date.year if movie.release_date else None
    show_inflation_adjusted = release_year is not None and release_year != date.today().year

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
        rotten_tomatoes_score=movie.rotten_tomatoes_score,
        metascore=movie.metascore,
        imdb_rating=movie.imdb_rating,
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
        budget_usd_inflation_adjusted=adjust_for_inflation(movie.budget_usd, release_year)
        if show_inflation_adjusted
        else None,
        domestic_gross_usd_inflation_adjusted=adjust_for_inflation(movie.domestic_gross_usd, release_year)
        if show_inflation_adjusted
        else None,
        worldwide_gross_usd_inflation_adjusted=adjust_for_inflation(movie.worldwide_gross_usd, release_year)
        if show_inflation_adjusted
        else None,
        inflation_adjusted_to_year=LATEST_CPI_YEAR if show_inflation_adjusted else None,
    )


@router.get("/{tmdb_id}/weekly-gross", response_model=list[WeeklyGrossPoint])
@limiter.limit(LOOKUP_RATE_LIMIT)
def get_weekly_gross(request: Request, tmdb_id: int, db: Session = Depends(get_db)) -> list[WeeklyGrossPoint]:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=404, detail="Movie not found") from exc

    observations = ingest_weekly_gross_from_boxofficemojo(db, movie)
    return [WeeklyGrossPoint.model_validate(obs) for obs in observations]


@router.get("/{tmdb_id}/compare/franchise", response_model=list[ComparisonSeries])
@limiter.limit(LOOKUP_RATE_LIMIT)
def compare_franchise(request: Request, tmdb_id: int, db: Session = Depends(get_db)) -> list[ComparisonSeries]:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=404, detail="Movie not found") from exc

    return get_franchise_comparison(db, movie)


@router.get("/{tmdb_id}/compare/year", response_model=list[ComparisonSeries])
@limiter.limit(LOOKUP_RATE_LIMIT)
def compare_year(request: Request, tmdb_id: int, db: Session = Depends(get_db)) -> list[ComparisonSeries]:
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        try:
            movie = upsert_movie_from_tmdb(db, tmdb_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=404, detail="Movie not found") from exc

    return get_same_year_comparison(db, movie)
