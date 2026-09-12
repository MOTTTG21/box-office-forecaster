from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Movie, MovieCredit, Person
from app.services.studio_registry import match_studio_slug
from app.services.tmdb_client import tmdb_client

TOP_CAST_LIMIT = 10


def upsert_movie_from_tmdb(db: Session, tmdb_id: int) -> Movie:
    """Fetch a movie + credits from TMDB and upsert it into the local DB.

    Raises httpx.HTTPError - a 404 (no such movie), a raw network failure, or the TMDB circuit
    breaker being open (app/services/circuit_breaker.py) all surface the same way, since callers
    already treat "TMDB didn't answer" as one case, not three.
    """
    data = tmdb_client.get_movie_with_credits(tmdb_id)

    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).one_or_none()
    if movie is None:
        movie = Movie(tmdb_id=tmdb_id)
        db.add(movie)

    movie.imdb_id = data.get("imdb_id")
    movie.title = data["title"]
    movie.original_title = data.get("original_title")
    movie.release_date = data.get("release_date") or None
    movie.status = "released" if data.get("status") == "Released" else "upcoming"
    movie.runtime_minutes = data.get("runtime") or None
    movie.budget_usd = data.get("budget") or None
    movie.genres = [genre["name"] for genre in data.get("genres", [])]
    collection = data.get("belongs_to_collection")
    movie.belongs_to_collection_tmdb_id = collection["id"] if collection else None
    movie.overview = data.get("overview")
    movie.poster_path = data.get("poster_path")
    movie.popularity_tmdb_snapshot = data.get("popularity")
    movie.popularity_snapshot_at = datetime.now(timezone.utc)
    movie.studio_slug = match_studio_slug(data.get("production_companies", []))

    db.flush()  # need movie.id before writing credits below

    _upsert_credits(db, movie, data.get("credits", {}))

    db.commit()
    db.refresh(movie)
    return movie


def _upsert_credits(db: Session, movie: Movie, credits: dict) -> None:
    db.query(MovieCredit).filter(MovieCredit.movie_id == movie.id).delete()

    directors = [c for c in credits.get("crew", []) if c.get("job") == "Director"]
    for director in directors:
        person = _upsert_person(db, director)
        db.add(MovieCredit(movie_id=movie.id, person_id=person.id, role="director"))

    cast = sorted(credits.get("cast", []), key=lambda c: c.get("order", 999))[:TOP_CAST_LIMIT]
    for member in cast:
        person = _upsert_person(db, member)
        db.add(
            MovieCredit(
                movie_id=movie.id,
                person_id=person.id,
                role="actor",
                cast_order=member.get("order"),
                character_name=member.get("character"),
            )
        )


def _upsert_person(db: Session, credit: dict) -> Person:
    tmdb_person_id = credit["id"]
    person = db.query(Person).filter(Person.tmdb_id == tmdb_person_id).one_or_none()
    if person is None:
        person = Person(
            tmdb_id=tmdb_person_id,
            name=credit["name"],
            known_for_department=credit.get("known_for_department"),
        )
        db.add(person)
        db.flush()
    return person
