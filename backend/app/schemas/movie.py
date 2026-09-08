from datetime import date

from pydantic import BaseModel, ConfigDict


class MovieSearchResult(BaseModel):
    tmdb_id: int
    title: str
    release_date: date | None = None
    poster_path: str | None = None


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    name: str
    character_name: str | None = None


class MovieDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    title: str
    overview: str | None = None
    release_date: date | None = None
    status: str
    runtime_minutes: int | None = None
    budget_usd: int | None = None
    genres: list[str] | None = None
    poster_path: str | None = None
    popularity_tmdb_snapshot: float | None = None
    director: PersonOut | None = None
    cast: list[PersonOut] = []
