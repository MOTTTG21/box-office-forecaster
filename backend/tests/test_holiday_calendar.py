from datetime import date

from app.services.holiday_calendar import _easter, get_holiday_highlight


def test_easter_lands_on_the_known_real_date_for_2024():
    # Easter Sunday 2024 was March 31, 2024 - a real, publicly verifiable date, not a guess
    assert _easter(2024) == date(2024, 3, 31)


def test_easter_lands_on_the_known_real_date_for_2025():
    assert _easter(2025) == date(2025, 4, 20)


def test_thanksgiving_week_is_flagged():
    # Thanksgiving 2026 is Nov 26 (4th Thursday) - box office week is Nov 23-29
    highlight = get_holiday_highlight(date(2026, 11, 23), date(2026, 11, 29))
    assert highlight is not None
    assert highlight.name == "thanksgiving"


def test_july_4th_week_is_flagged():
    highlight = get_holiday_highlight(date(2026, 6, 29), date(2026, 7, 5))
    assert highlight is not None
    assert highlight.name == "july_4th"


def test_a_quiet_week_returns_none():
    assert get_holiday_highlight(date(2026, 8, 10), date(2026, 8, 16)) is None


def test_christmas_week_is_flagged_as_christmas_not_generic_corridor():
    # 2023: Christmas Day is a Monday, so the box office week Dec 25-31 contains it exactly
    highlight = get_holiday_highlight(date(2023, 12, 25), date(2023, 12, 31))
    assert highlight is not None
    assert highlight.name == "christmas"


def test_corridor_catches_a_week_that_touches_the_corridor_without_the_exact_holiday_days():
    # the week right before Christmas week (in a year where Christmas falls on a Monday)
    # contains Dec 24 but neither Dec 25 nor Jan 1 - only the range-overlap check catches this
    highlight = get_holiday_highlight(date(2023, 12, 18), date(2023, 12, 24))
    assert highlight is not None
    assert highlight.name == "christmas_new_year_corridor"


def test_week_straddling_dec_31_jan_1_checks_both_years():
    # box office week Dec 29 2025 - Jan 4 2026 contains Jan 1 2026 - only findable by checking
    # window_end.year (2026), not window_start.year (2025)
    highlight = get_holiday_highlight(date(2025, 12, 29), date(2026, 1, 4))
    assert highlight is not None
    assert highlight.name == "new_years_day"
