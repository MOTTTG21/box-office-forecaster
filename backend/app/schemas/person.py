from datetime import date

from pydantic import BaseModel


class PersonSearchResult(BaseModel):
    tmdb_id: int
    name: str
    profile_path: str | None = None
    known_for_department: str | None = None


class FilmographyItem(BaseModel):
    tmdb_id: int
    title: str
    poster_path: str | None = None
    release_date: date | None = None
    role: str


class PersonDetail(BaseModel):
    tmdb_id: int
    name: str
    profile_path: str | None = None
    known_for_department: str | None = None
    biography: str | None = None
    filmography: list[FilmographyItem]
