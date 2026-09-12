"""Aggregates each tracked studio's theatrical slate for a calendar year into estimated
gross/budget/profit totals. There's no public per-film P&L to sum - studios are segments inside
public parent companies and only disclose quarterly segment totals, never per-movie - so this
reuses the same 2.5x-worldwide-multiple breakeven heuristic already used per-movie elsewhere in
the app (app/services/profitability.py), rolled up across a studio's slate. It's an estimate of
an estimate, and the UI says so.

To make the slate genuinely comprehensive rather than an accidental sample of whatever movies
this app happened to have already ingested, this discovers each studio's real releases for the
year via TMDB (with_companies) and upserts them - the same "discover, then upsert on demand"
pattern _new_release_entries already uses in app/routers/movies.py, just scoped by studio+year
instead of by this week's release window.

Discovery (across studios) and lifetime-gross scraping (across movies) both run concurrently via
run_with_isolated_sessions, not one item at a time - sequentially, this endpoint was slow enough
on a cold cache to exceed Vercel's serverless function timeout in production (a real incident:
"Failed to load studio slate" errors traced to this endpoint alone taking 20+ seconds).
"""

from datetime import date

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.etl.ingest_tmdb import upsert_movie_from_tmdb
from app.etl.scrape_boxofficemojo import ingest_lifetime_grosses
from app.models import Movie
from app.schemas.studio import StudioSlateMovie, StudioSlateReport, StudioSlateSummary
from app.services.concurrency import MAX_ITEMS_PER_REQUEST, run_with_isolated_sessions
from app.services.profitability import estimate_profit_usd
from app.services.studio_registry import Studio, all_studios
from app.services.theatrical_release import is_real_theatrical_release
from app.services.tmdb_client import tmdb_client


def _discover_and_upsert_slate(db: Session, tmdb_company_ids: tuple[int, ...], year: int) -> None:
    start = date(year, 1, 1).isoformat()
    end = date(year, 12, 31).isoformat()
    seen_tmdb_ids: set[int] = set()

    for company_id in tmdb_company_ids:
        try:
            candidates = tmdb_client.discover_movies_by_company_and_year(company_id, start, end)
        except httpx.HTTPError:
            continue
        for result in candidates:
            tmdb_id = result["id"]
            if tmdb_id in seen_tmdb_ids:
                continue
            seen_tmdb_ids.add(tmdb_id)
            existing = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
            if existing is not None:
                continue  # already ingested; re-fetching every request would be wasteful
            try:
                upsert_movie_from_tmdb(db, tmdb_id)
            except httpx.HTTPError:
                continue
            except IntegrityError:
                # a concurrent request (a real one found live in Railway logs: 3 real 500s on
                # /api/studios/slate?year=2026, the current year, where new inserts are still
                # happening) already inserted this tmdb_id between our check above and our
                # insert - it exists now, which is all we need.
                db.rollback()
                continue


def summarize_studio_slate(studio: Studio, movies: list[Movie]) -> StudioSlateSummary:
    """Pure aggregation over an already-fetched movie list - kept separate from the DB/network
    orchestration above so it's unit-testable without a database (this project has no test-DB
    fixtures; see the other services' test files for the same split)."""
    theatrical_movies = sorted(
        (m for m in movies if is_real_theatrical_release(m)), key=lambda m: m.release_date or date.min
    )

    budgets = [m.budget_usd for m in theatrical_movies if m.budget_usd]
    grosses_with_budget = [
        (m.budget_usd, m.worldwide_gross_usd) for m in theatrical_movies if m.budget_usd and m.worldwide_gross_usd
    ]

    return StudioSlateSummary(
        slug=studio.slug,
        display_name=studio.display_name,
        ticker=studio.ticker,
        release_count=len(theatrical_movies),
        movies_with_data=len(grosses_with_budget),
        total_budget_usd=sum(budgets) if budgets else None,
        total_worldwide_gross_usd=(sum(g for _, g in grosses_with_budget) if grosses_with_budget else None),
        movies=[
            StudioSlateMovie(tmdb_id=m.tmdb_id, title=m.title, poster_path=m.poster_path)
            for m in theatrical_movies
        ],
        estimated_profit_usd=(
            sum(estimate_profit_usd(b, g) for b, g in grosses_with_budget) if grosses_with_budget else None
        ),
    )


def _query_studio_movies(db: Session, studio_slug: str, year: int) -> list[Movie]:
    return (
        db.query(Movie)
        .filter(Movie.studio_slug == studio_slug)
        .filter(Movie.release_date.isnot(None))
        .filter(Movie.release_date >= date(year, 1, 1))
        .filter(Movie.release_date <= date(year, 12, 31))
        .all()
    )


def _ingest_lifetime_gross_by_id(session: Session, movie_id: int) -> None:
    movie = session.query(Movie).filter(Movie.id == movie_id).one_or_none()
    if movie is not None:
        ingest_lifetime_grosses(session, movie)


def get_studio_slate_summary(db: Session, year: int) -> StudioSlateReport:
    studios = all_studios()

    run_with_isolated_sessions(
        studios, lambda session, studio: _discover_and_upsert_slate(session, studio.tmdb_company_ids, year)
    )

    movies_by_studio = {studio.slug: _query_studio_movies(db, studio.slug, year) for studio in studios}

    needing_gross_ids = [
        movie.id
        for movies in movies_by_studio.values()
        for movie in movies
        if movie.status == "released" and movie.worldwide_gross_usd is None
    ]
    if needing_gross_ids:
        run_with_isolated_sessions(needing_gross_ids, _ingest_lifetime_gross_by_id, max_items=MAX_ITEMS_PER_REQUEST)
        movies_by_studio = {studio.slug: _query_studio_movies(db, studio.slug, year) for studio in studios}

    summaries = [summarize_studio_slate(studio, movies_by_studio[studio.slug]) for studio in studios]

    return StudioSlateReport(year=year, studios=summaries)
