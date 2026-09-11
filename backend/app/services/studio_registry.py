"""The fixed set of major studios this app tracks for the studio-slate and stock-comparison
features. Studio attribution comes from TMDB's production_companies list, matched by company id
rather than name (names get localized/reformatted; ids don't). A movie is credited to the first
recognized major studio in that list - TMDB doesn't expose an explicit "distributor" field, and
co-productions (e.g. Marvel + Sony on a Spider-Man film) list multiple companies, so this is an
approximation, disclosed wherever the aggregate is shown rather than presented as precise.

Tickers were verified live against Yahoo Finance before being hardcoded here, since several
changed recently: Paramount Pictures' parent trades as PSKY (Paramount Skydance Corporation)
after the 2025 Skydance merger, not the legacy PARA symbol - PARA now belongs to an unrelated
company. A studio with ticker=None (e.g. A24) has no public parent; callers must show "no public
parent company" rather than omitting it or fabricating a price.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Studio:
    slug: str
    display_name: str
    tmdb_company_ids: tuple[int, ...]
    ticker: str | None  # None = privately held, no public parent to compare against


STUDIOS: tuple[Studio, ...] = (
    Studio("disney", "Walt Disney Studios", (2, 420, 3, 127928), "DIS"),
    Studio("universal", "Universal Pictures", (33,), "CMCSA"),
    Studio("warner_bros", "Warner Bros. Pictures", (174, 12), "WBD"),
    Studio("sony", "Sony Pictures", (5,), "SONY"),
    Studio("paramount", "Paramount Pictures", (4,), "PSKY"),
    Studio("lionsgate", "Lionsgate", (1632,), "LION"),
    Studio("a24", "A24", (293354, 41077), None),
)

_ID_TO_SLUG: dict[int, str] = {cid: studio.slug for studio in STUDIOS for cid in studio.tmdb_company_ids}
_SLUG_TO_STUDIO: dict[str, Studio] = {studio.slug: studio for studio in STUDIOS}


def match_studio_slug(production_companies: list[dict]) -> str | None:
    """The slug of the first recognized major studio in TMDB's production_companies list, in
    the order TMDB returns them, or None if no company in the list is one this app tracks."""
    for company in production_companies:
        slug = _ID_TO_SLUG.get(company.get("id"))
        if slug:
            return slug
    return None


def get_studio(slug: str) -> Studio | None:
    return _SLUG_TO_STUDIO.get(slug)


def all_studios() -> tuple[Studio, ...]:
    return STUDIOS
