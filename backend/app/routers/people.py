from datetime import date

import httpx
from fastapi import APIRouter, HTTPException

from app.schemas.person import FilmographyItem, PersonDetail, PersonSearchResult
from app.services.tmdb_client import tmdb_client

router = APIRouter(prefix="/api/people", tags=["people"])

# Crew credits beyond these get noisy fast for prolific people (TMDB includes jobs like
# "Thanks" or "Post Production Supervisor"); this is the notable subset, in priority order
# for people who hold more than one crew role on the same film.
CREW_JOB_PRIORITY = ["Director", "Writer", "Screenplay", "Story", "Producer", "Executive Producer"]


def _build_filmography(credits: dict) -> list[FilmographyItem]:
    best: dict[int, FilmographyItem] = {}
    best_priority: dict[int, int] = {}

    for c in credits.get("crew", []):
        job = c.get("job")
        if job not in CREW_JOB_PRIORITY or not c.get("release_date") or not c.get("id"):
            continue
        priority = CREW_JOB_PRIORITY.index(job)
        if c["id"] not in best_priority or priority < best_priority[c["id"]]:
            best_priority[c["id"]] = priority
            best[c["id"]] = FilmographyItem(
                tmdb_id=c["id"],
                title=c.get("title") or "",
                poster_path=c.get("poster_path"),
                release_date=c["release_date"],
                role=job,
            )

    for c in credits.get("cast", []):
        if not c.get("release_date") or not c.get("id") or c["id"] in best:
            continue
        best[c["id"]] = FilmographyItem(
            tmdb_id=c["id"],
            title=c.get("title") or "",
            poster_path=c.get("poster_path"),
            release_date=c["release_date"],
            role=f"as {c['character']}" if c.get("character") else "Actor",
        )

    return sorted(best.values(), key=lambda item: item.release_date or date.min, reverse=True)


@router.get("/search", response_model=list[PersonSearchResult])
def search_people(q: str) -> list[PersonSearchResult]:
    return [
        PersonSearchResult(
            tmdb_id=result["id"],
            name=result["name"],
            profile_path=result.get("profile_path"),
            known_for_department=result.get("known_for_department"),
        )
        for result in tmdb_client.search_people(q)
        if result.get("name")
    ]


@router.get("/{tmdb_id}", response_model=PersonDetail)
def get_person(tmdb_id: int) -> PersonDetail:
    try:
        details = tmdb_client.get_person(tmdb_id)
        credits = tmdb_client.get_person_movie_credits(tmdb_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=404, detail="Person not found") from exc

    return PersonDetail(
        tmdb_id=details["id"],
        name=details["name"],
        profile_path=details.get("profile_path"),
        known_for_department=details.get("known_for_department"),
        biography=details.get("biography") or None,
        filmography=_build_filmography(credits),
    )
