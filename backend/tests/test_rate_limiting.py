"""Regression test for a real bug: slowapi's `default_limits` + `SlowAPIMiddleware` looked like
a global safety net for any route without an explicit @limiter.limit(...) decorator, but in
practice (verified against a live server) an undecorated route was completely unprotected - 110
rapid requests to an undecorated endpoint all returned 200. The only mechanism that reliably
works is decorating every route explicitly (or @limiter.exempt for the rare intentional
exception, e.g. the health check).

This test guards against that regression reappearing silently: every route this app defines must
be either rate-limited or explicitly marked exempt - there is no third, accidental state.
"""

from app.core.limiter import limiter
from app.main import app


def test_every_app_route_is_rate_limited_or_explicitly_exempt():
    unclassified = []
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None or not endpoint.__module__.startswith("app.routers"):
            continue  # not one of our routes (e.g. FastAPI's own /docs, /openapi.json)

        name = f"{endpoint.__module__}.{endpoint.__name__}"
        if name not in limiter._route_limits and name not in limiter._exempt_routes:
            unclassified.append(f"{route.path} ({name})")

    assert not unclassified, (
        "these routes have no rate limit and are not explicitly exempt - "
        f"decorate with @limiter.limit(...) or @limiter.exempt: {unclassified}"
    )
