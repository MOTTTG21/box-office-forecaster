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

    def get_movie_list(self, path: str) -> list[dict]:
        response = self._client.get(path)
        response.raise_for_status()
        return response.json()["results"]

    def get_movie_with_credits(self, tmdb_id: int) -> dict:
        response = self._client.get(f"/movie/{tmdb_id}", params={"append_to_response": "credits"})
        response.raise_for_status()
        return response.json()

    def get_person_movie_credits(self, person_tmdb_id: int) -> dict:
        response = self._client.get(f"/person/{person_tmdb_id}/movie_credits")
        response.raise_for_status()
        return response.json()

    def get_person(self, person_tmdb_id: int) -> dict:
        response = self._client.get(f"/person/{person_tmdb_id}")
        response.raise_for_status()
        return response.json()

    def search_people(self, query: str) -> list[dict]:
        response = self._client.get("/search/person", params={"query": query})
        response.raise_for_status()
        return response.json()["results"]

    def get_collection(self, collection_id: int) -> dict:
        response = self._client.get(f"/collection/{collection_id}")
        response.raise_for_status()
        return response.json()

    def discover_movies_by_date_range(self, start_date: str, end_date: str) -> list[dict]:
        response = self._client.get(
            "/discover/movie",
            params={
                "region": "US",
                "sort_by": "popularity.desc",
                "with_release_type": "2|3",
                "primary_release_date.gte": start_date,
                "primary_release_date.lte": end_date,
            },
        )
        response.raise_for_status()
        return response.json()["results"]

    def discover_movies_by_company_and_year(self, company_id: int, start_date: str, end_date: str) -> list[dict]:
        response = self._client.get(
            "/discover/movie",
            params={
                "region": "US",
                "sort_by": "primary_release_date.asc",
                "with_release_type": "2|3",
                "with_companies": company_id,
                "primary_release_date.gte": start_date,
                "primary_release_date.lte": end_date,
            },
        )
        response.raise_for_status()
        return response.json()["results"]


tmdb_client = TMDBClient()
