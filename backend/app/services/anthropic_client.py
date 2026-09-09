from dataclasses import dataclass, field

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

DEMOGRAPHICS_MAX_TOKENS = 1024
DEMOGRAPHICS_MAX_SEARCHES = 3

REPORT_DEMOGRAPHICS_TOOL = {
    "name": "report_demographics",
    "description": (
        "Report the audience demographic breakdown found via trade-press reporting of exit "
        "polls (PostTrak/CinemaScore), or that none was found."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "found_any_data": {
                "type": "boolean",
                "description": (
                    "True only if you found real trade-press-reported demographic data for "
                    "this specific film's opening weekend. False if you found nothing - do not "
                    "guess or estimate."
                ),
            },
            "percent_female": {
                "type": "number",
                "description": "Percent of opening-weekend audience that was female, 0-100. Omit if not reported.",
            },
            "percent_male": {
                "type": "number",
                "description": "Percent of opening-weekend audience that was male, 0-100. Omit if not reported.",
            },
            "percent_under_25": {
                "type": "number",
                "description": "Percent of audience under 25, 0-100 - only if the source used this exact age cut.",
            },
            "percent_25_and_over": {
                "type": "number",
                "description": "Percent of audience 25 and over, 0-100 - only if the source used this exact cut.",
            },
            "race_ethnicity_breakdown": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "group": {"type": "string"},
                        "percent": {"type": "number"},
                    },
                    "required": ["group", "percent"],
                },
                "description": (
                    "Race/ethnicity breakdown exactly as reported, using whatever category "
                    "labels the source itself used. Omit or leave empty if not reported."
                ),
            },
            "source_note": {
                "type": "string",
                "description": "Brief citation of which outlet/source reported this, e.g. 'PostTrak via Deadline'.",
            },
        },
        "required": ["found_any_data"],
    },
}

DEMOGRAPHICS_SYSTEM_PROMPT = (
    "You research real audience demographic data for movies, sourced only from trade-press "
    "reporting (Deadline, Variety, The Hollywood Reporter, etc.) of PostTrak or CinemaScore exit "
    "poll breakdowns for a film's opening weekend. Search for this specific film's opening "
    "weekend demographic breakdown. Then call report_demographics. If you find real reported "
    "numbers, report them exactly as the source stated them - never estimate, infer, or fill in "
    "a plausible-sounding number for a field the source didn't report; leave that field out "
    "instead. If a source uses a different age split than under-25/25-and-over, leave those age "
    "fields out rather than force a lossy conversion. If you find nothing after searching, call "
    "report_demographics with found_any_data=false rather than guessing. Never skip the tool "
    "call."
)


@dataclass
class DemographicsResult:
    found_any_data: bool
    percent_female: float | None = None
    percent_male: float | None = None
    percent_under_25: float | None = None
    percent_25_and_over: float | None = None
    race_ethnicity_breakdown: list[dict] = field(default_factory=list)
    source_note: str | None = None


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

    def research_audience_demographics(self, movie_title: str) -> DemographicsResult | None:
        """Researches a film's opening-weekend audience demographics via Claude's web_search
        tool, reported through a forced tool call - same shape as research_news_adjustment.
        Returns None if Claude never calls the tool at all (a genuine research failure); returns
        a DemographicsResult with found_any_data=False (not None) when Claude searched and
        explicitly found nothing to report - that's a normal, expected outcome for most films,
        not a failure."""
        response = self._client.post(
            "/v1/messages",
            json={
                "model": EXPLANATION_MODEL,
                "max_tokens": DEMOGRAPHICS_MAX_TOKENS,
                "system": DEMOGRAPHICS_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": f"Movie: {movie_title}"}],
                "tools": [
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": DEMOGRAPHICS_MAX_SEARCHES,
                    },
                    REPORT_DEMOGRAPHICS_TOOL,
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

        for block in data.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == "report_demographics":
                tool_input = block.get("input", {})
                try:
                    found_any_data = bool(tool_input["found_any_data"])
                except (KeyError, TypeError):
                    return None
                if not found_any_data:
                    return DemographicsResult(found_any_data=False)
                return DemographicsResult(
                    found_any_data=True,
                    percent_female=tool_input.get("percent_female"),
                    percent_male=tool_input.get("percent_male"),
                    percent_under_25=tool_input.get("percent_under_25"),
                    percent_25_and_over=tool_input.get("percent_25_and_over"),
                    race_ethnicity_breakdown=tool_input.get("race_ethnicity_breakdown") or [],
                    source_note=tool_input.get("source_note"),
                )
        return None


anthropic_client = AnthropicClient()
