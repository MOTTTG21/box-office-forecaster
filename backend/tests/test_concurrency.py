from app.services import concurrency


class _FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_runs_work_for_every_item(monkeypatch):
    monkeypatch.setattr(concurrency, "SessionLocal", lambda: _FakeSession())
    seen: list[int] = []

    concurrency.run_with_isolated_sessions([1, 2, 3], lambda session, item: seen.append(item))

    assert sorted(seen) == [1, 2, 3]


def test_each_item_gets_its_own_session_which_gets_closed(monkeypatch):
    sessions_used: list[_FakeSession] = []

    def _fake_session_factory():
        session = _FakeSession()
        sessions_used.append(session)
        return session

    monkeypatch.setattr(concurrency, "SessionLocal", _fake_session_factory)

    concurrency.run_with_isolated_sessions([1, 2, 3], lambda session, item: None)

    assert len(sessions_used) == 3
    assert all(session.closed for session in sessions_used)


def test_one_items_exception_does_not_crash_the_batch(monkeypatch):
    monkeypatch.setattr(concurrency, "SessionLocal", lambda: _FakeSession())
    seen: list[int] = []

    def work(session, item):
        if item == 2:
            raise RuntimeError("boom")
        seen.append(item)

    concurrency.run_with_isolated_sessions([1, 2, 3], work)  # must not raise

    assert sorted(seen) == [1, 3]


def test_empty_items_never_opens_a_session(monkeypatch):
    opened = []
    monkeypatch.setattr(concurrency, "SessionLocal", lambda: opened.append(1))

    concurrency.run_with_isolated_sessions([], lambda session, item: None)

    assert opened == []


def test_max_items_defers_the_rest_instead_of_processing_everything(monkeypatch):
    # Real production incident: a heavily-populated year (2022, 45 movies missing gross data)
    # took ~58s with no cap - right at the edge of a serverless timeout. max_items bounds it.
    monkeypatch.setattr(concurrency, "SessionLocal", lambda: _FakeSession())
    seen: list[int] = []

    concurrency.run_with_isolated_sessions(
        [1, 2, 3, 4, 5], lambda session, item: seen.append(item), max_items=2
    )

    assert len(seen) == 2


def test_max_items_none_processes_everything(monkeypatch):
    monkeypatch.setattr(concurrency, "SessionLocal", lambda: _FakeSession())
    seen: list[int] = []

    concurrency.run_with_isolated_sessions([1, 2, 3], lambda session, item: seen.append(item), max_items=None)

    assert sorted(seen) == [1, 2, 3]
