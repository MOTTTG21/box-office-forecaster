from datetime import datetime, timezone

import httpx

from app.models import Movie
from app.services import demographics_service as service_module
from app.services.anthropic_client import DemographicsResult
from app.services.demographics_service import ingest_audience_demographics


class _FakeSession:
    """A stand-in for a real DB session's commit()/refresh() - the field-setting logic being
    tested here mutates an existing Movie object in place, so neither call needs to do
    anything real for this test to exercise the actual behavior."""

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def _movie() -> Movie:
    return Movie(id=1, tmdb_id=1, title="Test Movie", status="released")


def test_found_data_populates_all_fields_and_sets_checked_at(monkeypatch):
    result = DemographicsResult(
        found_any_data=True,
        percent_female=55.0,
        percent_male=45.0,
        percent_under_25=30.0,
        percent_25_and_over=70.0,
        race_ethnicity_breakdown=[{"group": "White", "percent": 50.0}, {"group": "Hispanic", "percent": 25.0}],
        source_note="PostTrak via Deadline",
    )
    monkeypatch.setattr(service_module.anthropic_client, "research_audience_demographics", lambda title: result)

    movie = _movie()
    ingest_audience_demographics(_FakeSession(), movie)

    assert movie.demographic_percent_female == 55.0
    assert movie.demographic_percent_male == 45.0
    assert movie.demographic_percent_under_25 == 30.0
    assert movie.demographic_percent_25_and_over == 70.0
    assert movie.demographic_race_breakdown == [
        {"group": "White", "percent": 50.0},
        {"group": "Hispanic", "percent": 25.0},
    ]
    assert movie.demographic_source_note == "PostTrak via Deadline"
    assert movie.demographics_checked_at is not None


def test_not_found_leaves_fields_null_but_still_sets_checked_at(monkeypatch):
    result = DemographicsResult(found_any_data=False)
    monkeypatch.setattr(service_module.anthropic_client, "research_audience_demographics", lambda title: result)

    movie = _movie()
    ingest_audience_demographics(_FakeSession(), movie)

    assert movie.demographic_percent_female is None
    assert movie.demographic_race_breakdown is None
    assert movie.demographics_checked_at is not None


def test_already_checked_movie_never_calls_anthropic_client_again(monkeypatch):
    def _raise_if_called(title: str):
        raise AssertionError("should not be called for an already-checked movie")

    monkeypatch.setattr(service_module.anthropic_client, "research_audience_demographics", _raise_if_called)

    movie = _movie()
    movie.demographics_checked_at = datetime.now(timezone.utc)

    result = ingest_audience_demographics(_FakeSession(), movie)

    assert result is movie  # returned unchanged, no crash


def test_http_error_does_not_propagate_or_set_checked_at(monkeypatch):
    def _raise(title: str):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(service_module.anthropic_client, "research_audience_demographics", _raise)

    movie = _movie()
    ingest_audience_demographics(_FakeSession(), movie)

    # real behavior this guards: a transient failure must be retried later, not permanently
    # recorded as "checked, nothing found"
    assert movie.demographics_checked_at is None


def test_claude_never_calling_the_tool_also_does_not_set_checked_at(monkeypatch):
    monkeypatch.setattr(service_module.anthropic_client, "research_audience_demographics", lambda title: None)

    movie = _movie()
    ingest_audience_demographics(_FakeSession(), movie)

    assert movie.demographics_checked_at is None
