"""Regression test for a real production incident: two concurrent requests could both see "no
snapshot for today yet," both compute, and the second to commit crashed the whole request with
an IntegrityError on the (movie_id, week_number, snapshot_date) unique constraint. Verifies the
retry-by-rereading-the-winner logic without needing a real database - a fake Session is enough
to exercise the exact branch that failed in production.
"""

from sqlalchemy.exc import IntegrityError

from app.services.prediction_snapshot_service import get_or_record_snapshot


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self._result


class _FakeSnapshot:
    def __init__(self, predicted_weekend_gross_usd: float):
        self.predicted_weekend_gross_usd = predicted_weekend_gross_usd


class _RaceConditionSession:
    """Simulates: nothing exists on the first read, but by the time we try to commit, another
    request already won and inserted the real row - exactly what happened in production."""

    def __init__(self, winner_value: float):
        self._winner_value = winner_value
        self._queried_once = False
        self.rolled_back = False
        self.added = []

    def query(self, _model):
        if not self._queried_once:
            self._queried_once = True
            return _FakeQuery(None)
        return _FakeQuery(_FakeSnapshot(self._winner_value))

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        raise IntegrityError("duplicate key", params=None, orig=Exception("duplicate key"))

    def rollback(self):
        self.rolled_back = True


def test_returns_the_winning_concurrent_requests_value_instead_of_crashing():
    session = _RaceConditionSession(winner_value=42_000_000.0)

    result = get_or_record_snapshot(
        session,
        movie_id=1,
        week_number=1,
        is_new_release=True,
        compute_prediction=lambda: (99_000_000.0, "this request's own computed value, should be discarded"),
    )

    assert result == 42_000_000.0
    assert session.rolled_back is True


def test_falls_back_to_own_computed_value_if_the_winner_cannot_be_found_either():
    class _NoWinnerSession(_RaceConditionSession):
        def query(self, _model):
            return _FakeQuery(None)

    session = _NoWinnerSession(winner_value=0.0)

    result = get_or_record_snapshot(
        session,
        movie_id=1,
        week_number=1,
        is_new_release=True,
        compute_prediction=lambda: (99_000_000.0, "reason"),
    )

    assert result == 99_000_000.0
    assert session.rolled_back is True
