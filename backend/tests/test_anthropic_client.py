import httpx
import pytest

from app.services.anthropic_client import AnthropicClient


def _client_returning(json_body: dict, status_code: int = 200) -> AnthropicClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=json_body)

    client = AnthropicClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.anthropic.com")
    return client


def test_complete_extracts_text_from_response():
    client = _client_returning({"content": [{"type": "text", "text": "  This looks wrong because X.  "}]})
    assert client.complete("some prompt") == "This looks wrong because X."


def test_complete_raises_on_http_error():
    client = _client_returning({"error": "unauthorized"}, status_code=401)
    with pytest.raises(httpx.HTTPStatusError):
        client.complete("some prompt")


def test_research_audience_demographics_parses_found_data():
    client = _client_returning(
        {
            "content": [
                {
                    "type": "tool_use",
                    "name": "report_demographics",
                    "input": {
                        "found_any_data": True,
                        "percent_female": 60.0,
                        "percent_male": 40.0,
                        "source_note": "PostTrak via Deadline",
                    },
                }
            ]
        }
    )
    result = client.research_audience_demographics("Some Movie")
    assert result is not None
    assert result.found_any_data is True
    assert result.percent_female == 60.0
    assert result.source_note == "PostTrak via Deadline"


def test_research_audience_demographics_parses_not_found():
    client = _client_returning(
        {"content": [{"type": "tool_use", "name": "report_demographics", "input": {"found_any_data": False}}]}
    )
    result = client.research_audience_demographics("Some Movie")
    assert result is not None
    assert result.found_any_data is False
    assert result.percent_female is None


def test_research_audience_demographics_returns_none_when_tool_never_called():
    client = _client_returning({"content": [{"type": "text", "text": "I couldn't find anything."}]})
    assert client.research_audience_demographics("Some Movie") is None


def test_research_audience_demographics_returns_none_on_malformed_input():
    # missing the required found_any_data field entirely - must not crash
    client = _client_returning(
        {"content": [{"type": "tool_use", "name": "report_demographics", "input": {"source_note": "oops"}}]}
    )
    assert client.research_audience_demographics("Some Movie") is None


def test_investigate_anomaly_parses_likely_error():
    client = _client_returning(
        {
            "content": [
                {
                    "type": "tool_use",
                    "name": "report_investigation",
                    "input": {
                        "likely_data_error": True,
                        "suggested_correction": "Worldwide gross should be $120M per Box Office Mojo.",
                        "source_note": "Box Office Mojo lifetime page",
                    },
                }
            ]
        }
    )
    result = client.investigate_anomaly("Some Movie", "domestic_exceeds_worldwide", "domestic $130M > worldwide $100M")
    assert result is not None
    assert result.likely_data_error is True
    assert result.suggested_correction == "Worldwide gross should be $120M per Box Office Mojo."
    assert result.source_note == "Box Office Mojo lifetime page"


def test_investigate_anomaly_parses_figures_check_out():
    client = _client_returning(
        {
            "content": [
                {
                    "type": "tool_use",
                    "name": "report_investigation",
                    "input": {
                        "likely_data_error": False,
                        "suggested_correction": "",
                        "source_note": "Wikipedia infobox confirms the flagged figures",
                    },
                }
            ]
        }
    )
    result = client.investigate_anomaly("Some Movie", "some_rule", "some detail")
    assert result is not None
    assert result.likely_data_error is False
    assert result.suggested_correction is None


def test_investigate_anomaly_returns_none_when_tool_never_called():
    client = _client_returning({"content": [{"type": "text", "text": "I couldn't find anything."}]})
    assert client.investigate_anomaly("Some Movie", "some_rule", "some detail") is None


def test_investigate_anomaly_returns_none_on_malformed_input():
    # missing the required likely_data_error field entirely - must not crash
    client = _client_returning(
        {"content": [{"type": "tool_use", "name": "report_investigation", "input": {"source_note": "oops"}}]}
    )
    assert client.investigate_anomaly("Some Movie", "some_rule", "some detail") is None
