"""Flags when the current box-office week contains (or overlaps) a notable US holiday or
holiday corridor - these historically swing theatrical attendance. Every blurb here is
qualitative ("historically a strong box office week"), never a fabricated precise percentage -
there's no validated dataset backing a specific number, and inventing one would be exactly the
kind of plausible-sounding placeholder this project avoids everywhere else (see
news_signal_service.py's docstring for the same principle applied to the news-buzz signal).
"""

from dataclasses import dataclass
from datetime import date, timedelta

MONDAY = 0
THURSDAY = 3


@dataclass
class HolidayHighlight:
    name: str
    label: str
    blurb: str


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """weekday: Monday=0 ... Sunday=6. n=1 for the 1st occurrence, -1 for the last."""
    if n > 0:
        first_of_month = date(year, month, 1)
        offset = (weekday - first_of_month.weekday()) % 7
        return first_of_month + timedelta(days=offset + 7 * (n - 1))

    next_month_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    last_of_month = next_month_first - timedelta(days=1)
    offset = (last_of_month.weekday() - weekday) % 7
    return last_of_month - timedelta(days=offset)


def _easter(year: int) -> date:
    """Easter Sunday via the Anonymous Gregorian algorithm (Meeus/Jones/Butcher) - a
    well-established, compact closed-form computation, not hand-waved arithmetic."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    leap_correction = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * leap_correction) // 451
    month = (h + leap_correction - 7 * m + 114) // 31
    day = ((h + leap_correction - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _fixed_holidays(year: int) -> list[tuple[date, HolidayHighlight]]:
    return [
        (
            date(year, 7, 4),
            HolidayHighlight(
                "july_4th",
                "Fourth of July",
                "Historically a strong box office week - a mid-summer holiday with high theater attendance.",
            ),
        ),
        (
            date(year, 10, 31),
            HolidayHighlight(
                "halloween", "Halloween", "Historically a strong week for horror releases in particular."
            ),
        ),
        (
            date(year, 6, 19),
            HolidayHighlight("juneteenth", "Juneteenth", "A federal holiday that can lift midweek attendance."),
        ),
        (
            date(year, 12, 25),
            HolidayHighlight("christmas", "Christmas", "One of the strongest box office weeks of the year."),
        ),
        (
            date(year, 1, 1),
            HolidayHighlight(
                "new_years_day", "New Year's Day", "Part of the historically strong Christmas-New Year's corridor."
            ),
        ),
    ]


def _nth_weekday_holidays(year: int) -> list[tuple[date, HolidayHighlight]]:
    return [
        (
            _nth_weekday_of_month(year, 1, MONDAY, 3),
            HolidayHighlight("mlk_day", "MLK Day", "A three-day weekend that can modestly lift attendance."),
        ),
        (
            _nth_weekday_of_month(year, 2, MONDAY, 3),
            HolidayHighlight(
                "presidents_day", "Presidents Day", "A three-day weekend that can modestly lift attendance."
            ),
        ),
        (
            _nth_weekday_of_month(year, 5, MONDAY, -1),
            HolidayHighlight(
                "memorial_day", "Memorial Day", "Traditionally the unofficial start of the summer box office season."
            ),
        ),
        (
            _nth_weekday_of_month(year, 9, MONDAY, 1),
            HolidayHighlight(
                "labor_day", "Labor Day", "Traditionally one of the slower box office weekends of the year."
            ),
        ),
        (
            _nth_weekday_of_month(year, 11, THURSDAY, 4),
            HolidayHighlight(
                "thanksgiving", "Thanksgiving", "Historically one of the strongest box office weeks of the year."
            ),
        ),
    ]


def _all_holidays_for_year(year: int) -> list[tuple[date, HolidayHighlight]]:
    easter_highlight = HolidayHighlight(
        "easter", "Easter", "A family-holiday weekend that can lift family-film attendance."
    )
    return [*_fixed_holidays(year), *_nth_weekday_holidays(year), (_easter(year), easter_highlight)]


def _christmas_new_year_corridor(window_start: date, window_end: date) -> HolidayHighlight | None:
    """Dec 25 and Jan 1 are exactly 7 days apart, so the discrete Christmas/New Year's Day
    checks above always cover the week each falls in - but a week that only touches the tail
    end of the corridor (e.g. ending Dec 24, the last shopping/lead-up day, when Christmas
    falls on a Monday) can overlap the corridor without containing either exact holiday. This
    catches that case."""
    for year in {window_start.year, window_end.year}:
        corridor_start = date(year, 12, 24)
        corridor_end = date(year + 1, 1, 1)
        if window_start <= corridor_end and window_end >= corridor_start:
            return HolidayHighlight(
                "christmas_new_year_corridor",
                "Christmas-New Year's Corridor",
                "Part of the historically strong stretch between Christmas and New Year's Day.",
            )
    return None


def get_holiday_highlight(window_start: date, window_end: date) -> HolidayHighlight | None:
    """Checks holidays computed for both window_start.year and window_end.year, since a box
    office week can straddle Dec 31 / Jan 1."""
    for year in {window_start.year, window_end.year}:
        for holiday_date, highlight in _all_holidays_for_year(year):
            if window_start <= holiday_date <= window_end:
                return highlight

    return _christmas_new_year_corridor(window_start, window_end)
