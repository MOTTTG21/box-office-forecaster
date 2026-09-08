import httpx

from app.core.config import settings

ANTHROPIC_BASE_URL = "https://api.anthropic.com"
ANTHROPIC_API_VERSION = "2023-06-01"
EXPLANATION_MODEL = "claude-haiku-4-5-20251001"
EXPLANATION_MAX_TOKENS = 120
NEWS_RESEARCH_MAX_TOKENS = 1024
NEWS_RESEARCH_MAX_SEARCHES = 3

REPORT_ADJUSTMENT_TOOL = {
    "name": "report_adjustment",
    "description": "Report the final buzz-based percentage adjustment and reason, after researching.",
    "input_schema": {
        "type": "object",
        "properties": {
            "percent_adjustment": {
                "type": "number",
                "description": (
                    "Percentage to nudge the baseline prediction by, e.g. 8.5 or -12. "
                    "Use 0 if nothing notable turned up."
                ),
            },
            "reason": {
                "type": "string",
                "description": "One plain sentence citing what specifically drove this adjustment.",
            },
        },
        "required": ["percent_adjustment", "reason"],
    },
}

NEWS_RESEARCH_SYSTEM_PROMPT = (
    "You help forecast a movie's box office performance by researching very recent news about "
    "it. Search for real, current news about the movie's box office run, critical reception, or "
    "any controversy/buzz from the last few days. Then call report_adjustment with a percentage "
    "nudge (positive or negative) to apply to an existing statistical baseline prediction, based "
    "ONLY on what you actually find - a quiet, unremarkable week should get an adjustment at or "
    "near 0, not a token nonzero number just to seem responsive. Never call report_adjustment "
    "without having searched first."
)


class AnthropicClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=ANTHROPIC_BASE_URL,
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": ANTHROPIC_API_VERSION,
                "content-type": "application/json",
            },
            timeout=45.0,
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

    def research_news_adjustment(self, movie_title: str) -> tuple[float, str] | None:
        """Researches recent news for a movie via Claude's web_search tool and asks it to
        report a percentage adjustment + one-sentence reason through a forced tool call rather
        than free text, so the result is always cleanly parseable. Returns None if Claude never
        calls the tool (a research failure, or web search disabled for the org) - the caller
        falls back to the unadjusted baseline prediction in that case."""
        response = self._client.post(
            "/v1/messages",
            json={
                "model": EXPLANATION_MODEL,
                "max_tokens": NEWS_RESEARCH_MAX_TOKENS,
                "system": NEWS_RESEARCH_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": f"Movie: {movie_title}"}],
                "tools": [
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": NEWS_RESEARCH_MAX_SEARCHES,
                    },
                    REPORT_ADJUSTMENT_TOOL,
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

        for block in data.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == "report_adjustment":
                tool_input = block.get("input", {})
                try:
                    return float(tool_input["percent_adjustment"]), str(tool_input["reason"])
                except (KeyError, TypeError, ValueError):
                    return None
        return None


anthropic_client = AnthropicClient()
