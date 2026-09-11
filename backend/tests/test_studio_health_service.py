from sqlalchemy.exc import IntegrityError

from app.models import Movie
from app.services.studio_health_service import _discover_and_upsert_slate, summarize_studio_slate
from app.services.studio_registry import get_studio
from app.services.tmdb_client import tmdb_client


def _movie(*, budget_usd=None, worldwide_gross_usd=None, runtime_minutes=120) -> Movie:
    return Movie(
        title="Test Movie",
        budget_usd=budget_usd,
        worldwide_gross_usd=worldwide_gross_usd,
        runtime_minutes=runtime_minutes,
    )


def test_totals_sum_across_movies_with_full_data():
    disney = get_studio("disney")
    movies = [
        _movie(budget_usd=100_000_000, worldwide_gross_usd=300_000_000),
        _movie(budget_usd=200_000_000, worldwide_gross_usd=200_000_000),
    ]

    summary = summarize_studio_slate(disney, movies)

    assert summary.release_count == 2
    assert summary.movies_with_data == 2
    assert summary.total_budget_usd == 300_000_000
    assert summary.total_worldwide_gross_usd == 500_000_000
    # movie 1: 300M - 100M*2.5 = 50M profit; movie 2: 200M - 200M*2.5 = -300M; sum = -250M
    assert summary.estimated_profit_usd == -250_000_000


def test_a_movie_missing_budget_counts_toward_release_count_but_not_totals():
    disney = get_studio("disney")
    movies = [_movie(budget_usd=None, worldwide_gross_usd=100_000_000)]

    summary = summarize_studio_slate(disney, movies)

    assert summary.release_count == 1
    assert summary.movies_with_data == 0
    assert summary.total_budget_usd is None
    assert summary.total_worldwide_gross_usd is None
    assert summary.estimated_profit_usd is None


def test_no_movies_returns_none_totals_not_zero():
    disney = get_studio("disney")

    summary = summarize_studio_slate(disney, [])

    assert summary.release_count == 0
    assert summary.total_budget_usd is None
    assert summary.estimated_profit_usd is None


def test_a_token_theatrical_tv_special_is_excluded_from_the_slate():
    disney = get_studio("disney")
    movies = [
        _movie(budget_usd=100_000_000, worldwide_gross_usd=300_000_000, runtime_minutes=120),
        _movie(budget_usd=1_000_000, worldwide_gross_usd=2_000_000, runtime_minutes=45),
    ]

    summary = summarize_studio_slate(disney, movies)

    assert summary.release_count == 1
    assert summary.total_budget_usd == 100_000_000


def test_summary_carries_the_studios_display_name_and_ticker():
    a24 = get_studio("a24")

    summary = summarize_studio_slate(a24, [])

    assert summary.slug == "a24"
    assert summary.display_name == "A24"
    assert summary.ticker is None


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self._result


class _ConcurrentInsertSession:
    """Simulates a real production incident (3 real 500s found in Railway logs on
    /api/studios/slate?year=2026): the existence check finds nothing, but another concurrent
    request already inserted the same tmdb_id by the time this one tries to."""

    def __init__(self):
        self.rolled_back = False

    def query(self, _model):
        return _FakeQuery(None)  # "doesn't exist yet" on every check in this test

    def rollback(self):
        self.rolled_back = True


def test_a_concurrent_insert_of_the_same_movie_is_recovered_not_crashed(monkeypatch):
    monkeypatch.setattr(
        tmdb_client, "discover_movies_by_company_and_year", lambda company_id, start, end: [{"id": 999}]
    )

    def _raise_integrity_error(db, tmdb_id):
        raise IntegrityError("duplicate key", params=None, orig=Exception("duplicate key"))

    monkeypatch.setattr(
        "app.services.studio_health_service.upsert_movie_from_tmdb", _raise_integrity_error
    )

    session = _ConcurrentInsertSession()

    _discover_and_upsert_slate(session, tmdb_company_ids=(2,), year=2026)  # must not raise

    assert session.rolled_back is True
