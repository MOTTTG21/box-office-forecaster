"""A per-service circuit breaker for the external hosts this app depends on (TMDB, OMDb, Box
Office Mojo, Yahoo Finance). After enough consecutive failures it fails fast instead of letting
every request pile up waiting on a host that's actually down, then periodically lets a single
trial request through to check for recovery - the standard pattern, deliberately simple rather
than a full three-state machine, since this app runs as one process (no shared store needed).

State lives in-process and is visible via GET /api/data-quality/reliability for real
introspection, not just internal behavior - it's meant to be looked at, not just relied on.
"""

import time
from dataclasses import dataclass
from threading import Lock

import httpx

_REGISTRY: dict[str, "CircuitBreaker"] = {}
_REGISTRY_LOCK = Lock()


class CircuitOpenError(httpx.HTTPError):
    """Raised instead of attempting a call while a circuit is open. Deliberately a subclass of
    httpx.HTTPError (the same base every httpx network/timeout error already is) rather than its
    own standalone exception, so every existing `except httpx.HTTPError:` / `except
    httpx.HTTPStatusError:` call site in this app degrades a breaker trip exactly the same way
    it already degrades a real network failure, with no call site left unaware of it."""


@dataclass
class _BreakerState:
    consecutive_failures: int = 0
    opened_at: float | None = None
    last_failure_reason: str | None = None
    total_trips: int = 0


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state = _BreakerState()
        self._lock = Lock()

    def _is_blocking(self) -> bool:
        if self._state.opened_at is None:
            return False
        return time.monotonic() - self._state.opened_at < self.cooldown_seconds

    def call(self, fn):
        with self._lock:
            if self._is_blocking():
                raise CircuitOpenError(f"{self.name} circuit is open")
        try:
            result = fn()
        except Exception as exc:
            self._record_failure(str(exc))
            raise
        else:
            self._record_success()
            return result

    def _record_failure(self, reason: str) -> None:
        with self._lock:
            self._state.consecutive_failures += 1
            self._state.last_failure_reason = reason[:200]
            if self._state.consecutive_failures >= self.failure_threshold:
                self._state.opened_at = time.monotonic()
                self._state.total_trips += 1

    def _record_success(self) -> None:
        with self._lock:
            self._state.consecutive_failures = 0
            self._state.opened_at = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": "open" if self._is_blocking() else "closed",
                "consecutive_failures": self._state.consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "total_trips": self._state.total_trips,
                "last_failure_reason": self._state.last_failure_reason,
            }


def get_breaker(name: str, failure_threshold: int = 3, cooldown_seconds: float = 60.0) -> CircuitBreaker:
    """Returns the shared breaker for this service name, creating it on first use."""
    with _REGISTRY_LOCK:
        if name not in _REGISTRY:
            _REGISTRY[name] = CircuitBreaker(name, failure_threshold, cooldown_seconds)
        return _REGISTRY[name]


def all_breaker_snapshots() -> list[dict]:
    with _REGISTRY_LOCK:
        breakers = list(_REGISTRY.values())
    return [b.snapshot() for b in breakers]
