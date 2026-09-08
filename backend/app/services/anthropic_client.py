import httpx

from app.core.config import settings

ANTHROPIC_BASE_URL = "https://api.anthropic.com"
ANTHROPIC_API_VERSION = "2023-06-01"
EXPLANATION_MODEL = "claude-haiku-4-5-20251001"
EXPLANATION_MAX_TOKENS = 120


class AnthropicClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=ANTHROPIC_BASE_URL,
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": ANTHROPIC_API_VERSION,
                "content-type": "application/json",
            },
            timeout=20.0,
        )

    def complete(self, prompt: str) -> str:
        response = self._client.post(
            "/v1/messages",
            json={
                "model": EXPLANATION_MODEL,
                "max_tokens": EXPLANATION_MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"].strip()


anthropic_client = AnthropicClient()
