from datetime import date

from app.services.studio_market_service import build_market_points


def test_indexes_both_series_to_pct_change_from_the_first_common_week():
    week1, week2 = date(2026, 1, 5), date(2026, 1, 12)
    box_office = {week1: 10_000_000, week2: 15_000_000}
    stock = {week1: 100.0, week2: 110.0}

    points = build_market_points(box_office, stock)

    assert len(points) == 2
    assert points[0].box_office_pct_change == 0
    assert points[0].stock_pct_change == 0
    assert points[1].box_office_pct_change == 50.0
    assert points[1].stock_pct_change == 10.0


def test_only_weeks_present_in_both_series_are_included():
    week1, week2, week3 = date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)
    box_office = {week1: 10_000_000, week3: 5_000_000}  # no week2 - studio had no release that week
    stock = {week1: 100.0, week2: 105.0, week3: 95.0}

    points = build_market_points(box_office, stock)

    assert [p.week_start_date for p in points] == [week1, week3]


def test_fewer_than_two_common_weeks_returns_no_points():
    week1 = date(2026, 1, 5)
    points = build_market_points({week1: 10_000_000}, {week1: 100.0})

    assert points == []


def test_no_overlap_returns_no_points():
    points = build_market_points({date(2026, 1, 5): 10_000_000}, {date(2026, 2, 2): 100.0})

    assert points == []
