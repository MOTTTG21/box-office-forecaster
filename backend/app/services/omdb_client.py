import httpx

from app.core.config import settings
from app.services.circuit_breaker import get_breaker

OMDB_BASE_URL = "https://www.omdbapi.com/"


class OMDbClient:
    def __init__(self) -> None:
        self._client = httpx.Client(base_url=OMDB_BASE_URL, timeout=10.0)
        self._breaker = get_breaker("omdb")

    def get_ratings_by_imdb_id(self, imdb_id: str) -> dict:
        def _request() -> dict:
            response = self._client.get("/", params={"i": imdb_id, "apikey": settings.omdb_api_key})
            response.raise_for_status()
            return response.json()

        data = self._breaker.call(_request)
        if data.get("Response") == "False":
            return {}
        return data


omdb_client = OMDbClient()
