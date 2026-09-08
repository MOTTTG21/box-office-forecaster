import httpx

from app.core.config import settings

OMDB_BASE_URL = "https://www.omdbapi.com/"


class OMDbClient:
    def __init__(self) -> None:
        self._client = httpx.Client(base_url=OMDB_BASE_URL, timeout=10.0)

    def get_ratings_by_imdb_id(self, imdb_id: str) -> dict:
        response = self._client.get("/", params={"i": imdb_id, "apikey": settings.omdb_api_key})
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "False":
            return {}
        return data


omdb_client = OMDbClient()
