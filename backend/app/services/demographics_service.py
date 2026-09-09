"""Fetches a new release's real audience demographic breakdown (gender/age/race), sourced only
from Claude researching actual trade-press reporting of PostTrak/CinemaScore exit polls - never
fabricated, never estimated. Mirrors the critic-scores checked_at gate in ingest_omdb.py, with
one deliberate difference: demographics_checked_at is only set on a DEFINITIVE answer from
Claude (data found, or explicitly searched and found nothing) - never on a transient
httpx.HTTPError, so a real API hiccup gets retried on a later /this-week load instead of being
permanently misrecorded as "checked, nothing there."
"""

from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models import Movie
from app.services.anthropic_client import anthropic_client


def ingest_audience_demographics(db: Session, movie: Movie) -> Movie:
    if movie.demographics_checked_at is not None:
        return movie

    try:
        result = anthropic_client.research_audience_demographics(movie.title)
    except httpx.HTTPError:
        # a real API/network failure, not a definitive "nothing found" - leave checked_at unset
        # so this gets retried on a later lookup rather than being stuck "checked" forever
        return movie

    if result is None:
        # Claude never called the tool at all - same treatment as an API failure, not a
        # definitive answer worth caching
        return movie

    if result.found_any_data:
        movie.demographic_percent_female = result.percent_female
        movie.demographic_percent_male = result.percent_male
        movie.demographic_percent_under_25 = result.percent_under_25
        movie.demographic_percent_25_and_over = result.percent_25_and_over
        movie.demographic_race_breakdown = result.race_ethnicity_breakdown or None
        movie.demographic_source_note = result.source_note

    movie.demographics_checked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(movie)
    return movie
