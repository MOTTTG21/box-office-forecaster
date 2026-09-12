import pytest

from app.services import circuit_breaker
from app.services.circuit_breaker import CircuitBreaker, CircuitOpenError, all_breaker_snapshots, get_breaker


class _FakeClock:
    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_starts_closed_and_lets_successful_calls_through():
    breaker = CircuitBreaker("test-service", failure_threshold=3, cooldown_seconds=60)

    result = breaker.call(lambda: "ok")

    assert result == "ok"
    assert breaker.snapshot()["state"] == "closed"


def test_opens_after_reaching_the_failure_threshold(monkeypatch):
    clock = _FakeClock()
    monkeypatch.setattr(circuit_breaker.time, "monotonic", clock)
    breaker = CircuitBreaker("test-service", failure_threshold=3, cooldown_seconds=60)

    def fail():
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            breaker.call(fail)
    assert breaker.snapshot()["state"] == "closed"  # not open yet - below threshold

    with pytest.raises(RuntimeError):
        breaker.call(fail)  # third consecutive failure trips it

    assert breaker.snapshot()["state"] == "open"
    assert breaker.snapshot()["total_trips"] == 1


def test_an_open_breaker_fails_fast_without_calling_the_function(monkeypatch):
    clock = _FakeClock()
    monkeypatch.setattr(circuit_breaker.time, "monotonic", clock)
    breaker = CircuitBreaker("test-service", failure_threshold=1, cooldown_seconds=60)
    calls = []

    def fail():
        calls.append(1)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        breaker.call(fail)
    assert len(calls) == 1

    with pytest.raises(CircuitOpenError):
        breaker.call(fail)
    assert len(calls) == 1  # the second call never actually ran fail()


def test_allows_a_trial_call_again_after_the_cooldown_elapses(monkeypatch):
    clock = _FakeClock()
    monkeypatch.setattr(circuit_breaker.time, "monotonic", clock)
    breaker = CircuitBreaker("test-service", failure_threshold=1, cooldown_seconds=60)

    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert breaker.snapshot()["state"] == "open"

    clock.advance(61)  # past the cooldown window

    result = breaker.call(lambda: "recovered")

    assert result == "recovered"
    assert breaker.snapshot()["state"] == "closed"


def test_a_success_resets_consecutive_failures():
    breaker = CircuitBreaker("test-service", failure_threshold=3, cooldown_seconds=60)

    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert breaker.snapshot()["consecutive_failures"] == 2

    breaker.call(lambda: "ok")

    assert breaker.snapshot()["consecutive_failures"] == 0
    assert breaker.snapshot()["state"] == "closed"


def test_get_breaker_returns_the_same_instance_for_the_same_name():
    a = get_breaker("shared-name-test")
    b = get_breaker("shared-name-test")

    assert a is b


def test_all_breaker_snapshots_includes_every_registered_breaker():
    get_breaker("snapshot-test-a")
    get_breaker("snapshot-test-b")

    names = {s["name"] for s in all_breaker_snapshots()}

    assert "snapshot-test-a" in names
    assert "snapshot-test-b" in names


def test_circuit_open_error_is_an_httpx_http_error():
    import httpx

    assert issubclass(CircuitOpenError, httpx.HTTPError)
