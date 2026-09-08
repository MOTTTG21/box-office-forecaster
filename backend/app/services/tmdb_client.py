import httpx

from app.core.config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"


class TMDBClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=TMDB_BASE_URL,
            params={"api_key": settings.tmdb_api_key},
            timeout=10.0,
        )

    def search_movies(self, query: str) -> list[dict]:
        response = self._client.get("/search/movie", params={"query": query})
        response.raise_for_status()
        return response.json()["results"]

    def get_movie_with_credits(self, tmdb_id: int) -> dict:
        response = self._client.get(f"/movie/{tmdb_id}", params={"append_to_response": "credits"})
        response.raise_for_status()
        return response.json()


tmdb_client = TMDBClient()
