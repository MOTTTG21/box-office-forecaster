import re
from datetime import date

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import Movie, WeeklyGrossObservation
from app.services.circuit_breaker import get_breaker

BOM_BASE_URL = "https://www.boxofficemojo.com"
_breaker = get_breaker("box_office_mojo")
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
    try:
        return int(text.replace("$", "").replace(",", ""))
    except ValueError:
        # BOM's markup for this cell didn't match the expected "$1,234" shape - treat it as
        # unknown rather than letting one odd cell take down the whole movie's ingestion
        return None


def _parse_int(text: str) -> int | None:
    text = text.strip()
    if not text or text == "-":
        return None
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None


def _find_domestic_weekend_url(client: httpx.Client, imdb_id: str) -> str | None:
    response = client.get(f"/title/{imdb_id}/")
    if response.status_code != 200:
        return None
    match = RELEASE_WEEKEND_RE.search(response.text)
    if not match:
        return None
    return f"{match.group(1)}/weekend/"


def _fetch_lifetime_grosses(client: httpx.Client, imdb_id: str) -> tuple[int | None, int | None]:
    """Returns (domestic, worldwide) lifetime gross from the movie's BOM title page summary."""
    response = client.get(f"/title/{imdb_id}/")
    if response.status_code != 200:
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    summary = soup.find("div", class_="mojo-performance-summary-table")
    if summary is None:
        return None, None

    domestic = worldwide = None
    for row in summary.find_all("div", class_="a-section", recursive=False):
        label = row.find("span", class_="a-size-small")
        money = row.find("span", class_="money")
        if label is None or money is None:
            continue
        label_text = label.get_text(strip=True)
        value = _parse_money(money.get_text(strip=True))
        if label_text.startswith("Domestic"):
            domestic = value
        elif label_text.startswith("Worldwide"):
            worldwide = value

    if worldwide is None:
        worldwide = domestic  # domestic-only release, no international breakout on BOM
    return domestic, worldwide


def _fetch_weekend_rows(client: httpx.Client, weekend_url: str, release_year: int) -> list[dict]:
    response = client.get(weekend_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table is None:
        return []

    rows = table.find_all("tr")[1:]  # skip header
    observations = []
    seen_week_numbers: set[int] = set()
    current_year = release_year
    prev_month = None

    for row in rows:
        date_cell = row.find("td")
        date_link = date_cell.find("a") if date_cell else None
        if date_link and "/occasion/" in (date_link.get("href") or ""):
            # supplementary holiday-window row (e.g. "Easter wknd") layered on top of a
            # regular week's row for the same date range - not a distinct week, skip it
            continue

        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if len(cells) < 9:
            continue

        week_number_text = cells[8].strip()
        if not week_number_text.isdigit():
            continue
        week_number = int(week_number_text)
        if week_number in seen_week_numbers:
            # defensive: guards against any other BOM table quirk producing a repeat
            # week number, which would otherwise violate our unique constraint
            continue
        seen_week_numbers.add(week_number)

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
                "week_number": week_number,
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

    def _scrape() -> list[dict]:
        with httpx.Client(base_url=BOM_BASE_URL, headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
            weekend_url = _find_domestic_weekend_url(client, movie.imdb_id)
            if weekend_url is None:
                return []
            release_year = movie.release_date.year if movie.release_date else date.today().year
            return _fetch_weekend_rows(client, weekend_url, release_year)

    rows = _breaker.call(_scrape)

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


def ingest_lifetime_grosses(db: Session, movie: Movie) -> Movie:
    """Scrape and store a movie's lifetime domestic/worldwide gross from Box Office Mojo. Cached on the movie row."""
    if movie.worldwide_gross_usd is not None or not movie.imdb_id:
        return movie

    def _scrape() -> tuple[int | None, int | None]:
        with httpx.Client(base_url=BOM_BASE_URL, headers={"User-Agent": USER_AGENT}, timeout=10.0) as client:
            return _fetch_lifetime_grosses(client, movie.imdb_id)

    domestic, worldwide = _breaker.call(_scrape)

    if domestic is not None:
        movie.domestic_gross_usd = domestic
    if worldwide is not None:
        movie.worldwide_gross_usd = worldwide
        db.commit()
        db.refresh(movie)
    return movie
