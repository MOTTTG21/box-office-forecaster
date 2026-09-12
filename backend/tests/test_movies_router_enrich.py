"""Tests the task-selection logic in _enrich_movie_concurrently - which independent per-movie
enrichers (lifetime-gross scrape, critic-score fetch) actually need to run, since that decision
is what makes a repeat movie view fast and a first-ever view only pay for what's missing.
"""

from app.etl.ingest_omdb import ingest_critic_scores
from app.etl.scrape_boxofficemojo import ingest_lifetime_grosses
from app.models import Movie
from app.routers.movies import _enrich_movie_concurrently


class _NoOpSession:
    def refresh(self, obj):
        pass


def _movie(*, status="released", worldwide_gross_usd=None, critic_scores_checked_at=None, imdb_id="tt1"):
    return Movie(
        tmdb_id=1,
        title="Test Movie",
        status=status,
        worldwide_gross_usd=worldwide_gross_usd,
        critic_scores_checked_at=critic_scores_checked_at,
        imdb_id=imdb_id,
    )


def test_fully_cached_movie_runs_no_tasks(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.movies.run_with_isolated_sessions", lambda tasks, work: calls.append(tasks)
    )
    movie = _movie(worldwide_gross_usd=100, critic_scores_checked_at="checked")

    _enrich_movie_concurrently(_NoOpSession(), movie)

    assert calls == []  # run_with_isolated_sessions never even called


def test_missing_gross_only_runs_one_task(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.movies.run_with_isolated_sessions", lambda tasks, work: calls.append(tasks)
    )
    movie = _movie(worldwide_gross_usd=None, critic_scores_checked_at="checked")

    _enrich_movie_concurrently(_NoOpSession(), movie)

    assert calls == [[ingest_lifetime_grosses]]


def test_missing_critic_scores_only_runs_one_task(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.movies.run_with_isolated_sessions", lambda tasks, work: calls.append(tasks)
    )
    movie = _movie(worldwide_gross_usd=100, critic_scores_checked_at=None)

    _enrich_movie_concurrently(_NoOpSession(), movie)

    assert calls == [[ingest_critic_scores]]


def test_a_brand_new_movie_runs_both_tasks(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.movies.run_with_isolated_sessions", lambda tasks, work: calls.append(tasks)
    )
    movie = _movie(worldwide_gross_usd=None, critic_scores_checked_at=None)

    _enrich_movie_concurrently(_NoOpSession(), movie)

    assert calls == [[ingest_lifetime_grosses, ingest_critic_scores]]


def test_an_unreleased_movie_never_needs_a_gross_scrape(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.movies.run_with_isolated_sessions", lambda tasks, work: calls.append(tasks)
    )
    movie = _movie(status="upcoming", worldwide_gross_usd=None, critic_scores_checked_at="checked")

    _enrich_movie_concurrently(_NoOpSession(), movie)

    assert calls == []


def test_no_imdb_id_never_needs_a_critic_score_fetch(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.movies.run_with_isolated_sessions", lambda tasks, work: calls.append(tasks)
    )
    movie = _movie(worldwide_gross_usd=100, critic_scores_checked_at=None, imdb_id=None)

    _enrich_movie_concurrently(_NoOpSession(), movie)

    assert calls == []
