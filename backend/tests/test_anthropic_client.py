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
