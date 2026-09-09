"""Applies a bounded, Claude-researched daily "buzz" adjustment on top of the base heuristic
prediction for a movie currently tracked in the Top 10 forecast.

This is explicitly experimental and never claimed as a validated accuracy improvement (labeled
as such wherever it's shown) - unlike the opening-weekend and decline models, there's no way to
backtest "would recent news buzz have predicted this movie's actual result," since historical
news-buzz data for old movies doesn't exist to test against. It's a real, live-researched signal
(not a guess dressed up as one), just an unvalidated one.

Claude researches via its web_search tool and reports a percentage nudge + one-sentence reason
through a forced tool call (see anthropic_client.research_news_adjustment) - never free text, so
the result is always parseable. The percentage is clamped to MAX_ADJUSTMENT_PCT regardless of
what Claude proposes, as a hard safety rail against one research pass swinging the number to
somewhere absurd.

If the call fails for any reason (no API key configured, rate limited, web search disabled for
the org), the snapshot just uses the unadjusted baseline - this signal is additive, never
required for the forecast to function.
"""

import httpx

from app.services.anthropic_client import anthropic_client

MAX_ADJUSTMENT_PCT = 25.0


def apply_news_adjustment(base_prediction: float | None, movie_title: str) -> tuple[float | None, str | None]:
    """Returns (adjusted_prediction, reason). Falls back to (base_prediction, None) unchanged
    if the base prediction is unknown or the research call doesn't produce a usable result.

    base_prediction can arrive as a decimal.Decimal (new-release predictions come straight from
    a SQLAlchemy Numeric column) or a plain float (holdover predictions, computed in Python) -
    coerced to float up front so both paths do the same arithmetic. A real bug this guards
    against: Decimal * float raises TypeError, which took the whole /this-week endpoint down in
    production the first time a new release needed a fresh (uncached) snapshot computed."""
    if base_prediction is None:
        return None, None
    base_prediction = float(base_prediction)

    try:
        result = anthropic_client.research_news_adjustment(movie_title)
    except httpx.HTTPError:
        return base_prediction, None

    if result is None:
        return base_prediction, None

    percent, reason = result
    clamped_pct = max(-MAX_ADJUSTMENT_PCT, min(MAX_ADJUSTMENT_PCT, percent))
    adjusted = base_prediction * (1 + clamped_pct / 100)
    return adjusted, reason
