import httpx

from app.models import Movie
from app.services import anthropic_client as anthropic_client_module
from app.services.anomaly_detection import Anomaly
from app.services.data_quality import _explain


def _anomaly() -> Anomaly:
    movie = Movie(id=1, tmdb_id=1, title="Test Movie", status="released")
    return Anomaly(movie=movie, rule_name="domestic_exceeds_worldwide", severity="high", detail="some detail")


def test_explain_returns_claude_text(monkeypatch):
    monkeypatch.setattr(
        anthropic_client_module.anthropic_client, "complete", lambda prompt: "It's impossible because X."
    )
    assert _explain(_anomaly()) == "It's impossible because X."


def test_explain_returns_none_when_api_call_fails(monkeypatch):
    def _raise(prompt: str) -> str:
        raise httpx.HTTPStatusError("boom", request=httpx.Request("POST", "https://x"), response=httpx.Response(401))

    monkeypatch.setattr(anthropic_client_module.anthropic_client, "complete", _raise)
    assert _explain(_anomaly()) is None
