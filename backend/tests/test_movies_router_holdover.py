"""_holdover_entries used to compute each holdover's snapshot (get_or_record_snapshot, which can
trigger a live Claude + web_search call via apply_news_adjustment) one movie at a time in a
sequential for-loop. Once ingest_weekly_gross_from_boxofficemojo started properly refreshing
stale holdover data instead of caching it forever, several movies' target_week could advance in
the same /this-week request, and each needed its own first-time Claude call in series - a real
76s request for ~10-15 movies. This mirrors the Studios/BOM fix: the snapshot computation now
also runs concurrently across movies via run_with_isolated_sessions, each with its own DB
session, the same pattern already used for the BOM re-scrape step just above it.
"""

import threading
from types import SimpleNamespace

from app.models import Movie
from app.routers import movies as movies_module
from app.services import concurrency


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def one_or_none(self):
        return self._result


class _FakeMovieDB:
    """Supports exactly the query shape `_holdover_entries` and its `_refresh`/`_snapshot`
    workers issue against Movie: `db.query(Movie).filter(Movie.<col> == value).one_or_none()`."""

    def __init__(self, movies: list[Movie]):
        self._movies = movies
        self.closed = False

    def query(self, model):
        assert model is Movie
        return self

    def filter(self, criterion):
        column_name = criterion.left.key
        value = criterion.right.value
        match = next((m for m in self._movies if getattr(m, column_name) == value), None)
        return _FakeQuery(match)

    def close(self):
        self.closed = True


def _movie(id_: int, tmdb_id: int, title: str) -> Movie:
    return Movie(id=id_, tmdb_id=tmdb_id, title=title, status="released", imdb_id=f"tt{id_}")


def _obs(week_number: int, weekend_gross_usd: float):
    return SimpleNamespace(week_number=week_number, weekend_gross_usd=weekend_gross_usd)


def _unadjusted_prediction(transitions, exclude_movie_id, target_week, prior_weekend_gross):
    return prior_weekend_gross


def _no_news_adjustment(base, title):
    return base, None, None


def test_holdover_snapshots_are_computed_through_isolated_sessions_not_the_request_session(monkeypatch):
    movies = [_movie(1, 101, "Movie A"), _movie(2, 102, "Movie B"), _movie(3, 103, "Movie C")]
    latest_gross_by_movie_id = {1: 100.0, 2: 200.0, 3: 300.0}
    observations_by_movie_id = {
        m.id: [_obs(1, latest_gross_by_movie_id[m.id])] for m in movies
    }

    request_db = _FakeMovieDB(movies)
    worker_sessions: list[_FakeMovieDB] = []

    def _fake_session_local():
        session = _FakeMovieDB(movies)
        worker_sessions.append(session)
        return session

    monkeypatch.setattr(concurrency, "SessionLocal", _fake_session_local)
    monkeypatch.setattr(movies_module.tmdb_client, "get_movie_list", lambda path: [{"id": m.tmdb_id} for m in movies])
    monkeypatch.setattr(movies_module, "load_transitions_from_db", lambda db: [])
    monkeypatch.setattr(movies_module, "is_real_theatrical_release", lambda movie: True)
    monkeypatch.setattr(
        movies_module, "ingest_weekly_gross_from_boxofficemojo", lambda db, movie: observations_by_movie_id[movie.id]
    )
    monkeypatch.setattr(movies_module, "predict_next_weekend_gross", _unadjusted_prediction)
    monkeypatch.setattr(movies_module, "apply_news_adjustment", _no_news_adjustment)

    snapshot_calls: list[tuple[int, object]] = []

    def _fake_get_or_record_snapshot(db, movie_id, week_number, is_new_release, compute_prediction):
        snapshot_calls.append((movie_id, db))
        predicted, _reason, _sentiment = compute_prediction()
        return predicted

    monkeypatch.setattr(movies_module, "get_or_record_snapshot", _fake_get_or_record_snapshot)

    entries = movies_module._holdover_entries(request_db, exclude_tmdb_ids=set())

    # every candidate's snapshot ran through its own isolated worker session, never the shared
    # per-request session and never sharing one session across two movies - the same
    # session-per-item guarantee run_with_isolated_sessions already gives the BOM refresh step
    # directly above this one. (worker_sessions also includes that BOM refresh step's own
    # sessions, since both steps draw from the same SessionLocal.)
    used_sessions = [db for _movie_id, db in snapshot_calls]
    assert len(used_sessions) == len(movies)
    assert len(set(used_sessions)) == len(movies)  # no two movies shared a session
    assert request_db not in used_sessions
    assert set(used_sessions) <= set(worker_sessions)

    # each movie's own predicted gross reaches its own entry - no cross-movie mixups introduced
    # by computing them concurrently instead of in the original sequential for-loop.
    by_tmdb_id = {e.tmdb_id: e for e in entries}
    assert by_tmdb_id[101].predicted_weekend_gross_usd == 100.0
    assert by_tmdb_id[102].predicted_weekend_gross_usd == 200.0
    assert by_tmdb_id[103].predicted_weekend_gross_usd == 300.0


def test_a_failing_snapshot_computation_does_not_take_down_the_other_movies(monkeypatch):
    movies = [_movie(1, 101, "Movie A"), _movie(2, 102, "Movie B")]
    observations_by_movie_id = {1: [_obs(1, 100.0)], 2: [_obs(1, 200.0)]}

    monkeypatch.setattr(concurrency, "SessionLocal", lambda: _FakeMovieDB(movies))
    monkeypatch.setattr(movies_module.tmdb_client, "get_movie_list", lambda path: [{"id": m.tmdb_id} for m in movies])
    monkeypatch.setattr(movies_module, "load_transitions_from_db", lambda db: [])
    monkeypatch.setattr(movies_module, "is_real_theatrical_release", lambda movie: True)
    monkeypatch.setattr(
        movies_module, "ingest_weekly_gross_from_boxofficemojo", lambda db, movie: observations_by_movie_id[movie.id]
    )
    monkeypatch.setattr(movies_module, "predict_next_weekend_gross", _unadjusted_prediction)
    monkeypatch.setattr(movies_module, "apply_news_adjustment", _no_news_adjustment)

    def _flaky_get_or_record_snapshot(db, movie_id, week_number, is_new_release, compute_prediction):
        if movie_id == 1:
            raise RuntimeError("simulated Claude API failure")
        predicted, _reason, _sentiment = compute_prediction()
        return predicted

    monkeypatch.setattr(movies_module, "get_or_record_snapshot", _flaky_get_or_record_snapshot)

    entries = movies_module._holdover_entries(_FakeMovieDB(movies), exclude_tmdb_ids=set())  # must not raise

    by_tmdb_id = {e.tmdb_id: e for e in entries}
    assert by_tmdb_id[101].predicted_weekend_gross_usd is None
    assert by_tmdb_id[102].predicted_weekend_gross_usd == 200.0


def test_snapshot_computations_actually_run_concurrently(monkeypatch):
    """Guards against a regression back to the sequential for-loop: with N movies each needing
    a "slow" first-time snapshot, wall-clock time should scale with N / MAX_WORKERS, not N."""
    n_movies = concurrency.MAX_WORKERS * 2
    movies = [_movie(i, 100 + i, f"Movie {i}") for i in range(n_movies)]
    observations_by_movie_id = {m.id: [_obs(1, 100.0 * m.id)] for m in movies}
    seen_threads: set[int] = set()
    lock = threading.Lock()

    monkeypatch.setattr(concurrency, "SessionLocal", lambda: _FakeMovieDB(movies))
    monkeypatch.setattr(movies_module.tmdb_client, "get_movie_list", lambda path: [{"id": m.tmdb_id} for m in movies])
    monkeypatch.setattr(movies_module, "load_transitions_from_db", lambda db: [])
    monkeypatch.setattr(movies_module, "is_real_theatrical_release", lambda movie: True)
    monkeypatch.setattr(
        movies_module, "ingest_weekly_gross_from_boxofficemojo", lambda db, movie: observations_by_movie_id[movie.id]
    )
    monkeypatch.setattr(movies_module, "predict_next_weekend_gross", _unadjusted_prediction)
    monkeypatch.setattr(movies_module, "apply_news_adjustment", _no_news_adjustment)

    def _slow_get_or_record_snapshot(db, movie_id, week_number, is_new_release, compute_prediction):
        with lock:
            seen_threads.add(threading.get_ident())
        import time

        time.sleep(0.05)
        predicted, _reason, _sentiment = compute_prediction()
        return predicted

    monkeypatch.setattr(movies_module, "get_or_record_snapshot", _slow_get_or_record_snapshot)

    movies_module._holdover_entries(_FakeMovieDB(movies), exclude_tmdb_ids=set())

    # more than one distinct thread actually did the work - i.e. this ran in parallel, not
    # one-item-at-a-time on the caller's own thread.
    assert len(seen_threads) > 1
