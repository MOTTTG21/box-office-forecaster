import re
from datetime import date

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import Movie, WeeklyGrossObservation

BOM_BASE_URL = "https://www.boxofficemojo.com"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 (personal portfolio project; non-commercial)"
)

MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

DATE_CELL_RE = re.compile(r"^([A-Za-z]{3})\w*\s+(\d{1,2})")
RELEASE_WEEKEND_RE = re.compile(r'href="(/release/rl\d+)/weekend')


def _parse_money(text: str) -> int | None:
    text = text.strip()
    if not text or text == "-":
        return None
    return int(text.replace("$", "").replace(",", ""))


def _parse_int(text: str) -> int | None:
    text = text.strip()
    if not text or text == "-":
        return None
    return int(text.replace(",", ""))


def _find_domestic_weekend_url(client: httpx.Client, imdb_id: str) -> str | None:
    response = client.get(f"/title/{imdb_id}/")
    if response.status_code != 200:
        return None
    match = RELEASE_WEEKEND_RE.search(response.text)
    if not match:
        return None
    return f"{match.group(1)}/weekend/"


def _fetch_weekend_rows(client: httpx.Client, weekend_url: str, release_year: int) -> list[dict]:
    response = client.get(weekend_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table is None:
        return []

    rows = table.find_all("tr")[1:]  # skip header
    observations = []
    current_year = release_year
    prev_month = None

    for row in rows:
        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if len(cells) < 9:
            continue

        week_number_text = cells[8].strip()
        if not week_number_text.isdigit():
            continue  # holiday-labeled duplicate row (e.g. "Labor Day wknd"), not a distinct week

        date_match = DATE_CELL_RE.match(cells[0])
        week_start_date = None
        if date_match:
            month = MONTHS.get(date_match.group(1))
            day = int(date_match.group(2))
            if month is not None:
                if prev_month is not None and month < prev_month:
                    current_year += 1
                prev_month = month
                week_start_date = date(current_year, month, day)

        observations.append(
            {
                "week_number": int(week_number_text),
                "week_start_date": week_start_date,
                "rank": _parse_int(cells[1]),
                "weekend_gross_usd": _parse_money(cells[2]),
                "theater_count": _parse_int(cells[4]),
                "cumulative_gross_usd": _parse_money(cells[7]),
            }
        )

    return observations


def ingest_weekly_gross_from_boxofficemojo(db: Session, movie: Movie) -> list[WeeklyGrossObservation]:
    """Scrape and store domestic weekend-by-weekend gross for a movie from Box Office Mojo.

    Only scrapes once per movie (checks for existing rows first) - fine for
    completed theatrical runs, which is what this covers for now. Returns
    the stored observations, ordered by week number.
    """
    existing = (
        db.query(WeeklyGrossObservation)
        .filter(
            WeeklyGrossObservation.movie_id == movie.id,
            WeeklyGrossObservation.source == "boxofficemojo_scrape",
        )
        .order_by(WeeklyGrossObservation.week_number)
        .all()
    )
    if existing:
        return existing

    if not movie.imdb_id:
        return []

    with httpx.Client(base_url=BOM_BASE_URL, headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
        weekend_url = _find_domestic_weekend_url(client, movie.imdb_id)
        if weekend_url is None:
            return []

        release_year = movie.release_date.year if movie.release_date else date.today().year
        rows = _fetch_weekend_rows(client, weekend_url, release_year)

    observations = [
        WeeklyGrossObservation(
            movie_id=movie.id,
            territory="domestic",
            source="boxofficemojo_scrape",
            **row,
        )
        for row in rows
    ]
    db.add_all(observations)
    db.commit()
    for obs in observations:
        db.refresh(obs)
    return observations
