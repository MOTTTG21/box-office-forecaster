from app.models import Movie, WeeklyGrossObservation
from app.services.anomaly_detection import (
    _check_domestic_exceeds_worldwide,
    _check_implausible_budget_for_wide_release,
    _check_implausible_runtime,
    _check_opening_weekend_exceeds_domestic_total,
    _genre_budget_to_gross_outliers,
)


def _movie(**kwargs) -> Movie:
    defaults = {"id": 1, "tmdb_id": 1, "title": "Test Movie", "status": "released"}
    return Movie(**{**defaults, **kwargs})


def test_flags_domestic_exceeding_worldwide():
    movie = _movie(domestic_gross_usd=50_000_000, worldwide_gross_usd=40_000_000)
    anomaly = _check_domestic_exceeds_worldwide(movie)
    assert anomaly is not None
    assert anomaly.rule_name == "domestic_exceeds_worldwide"
    assert anomaly.severity == "high"


def test_does_not_flag_when_worldwide_is_larger():
    movie = _movie(domestic_gross_usd=40_000_000, worldwide_gross_usd=100_000_000)
    assert _check_domestic_exceeds_worldwide(movie) is None


def test_does_not_flag_domestic_when_either_gross_missing():
    assert _check_domestic_exceeds_worldwide(_movie(domestic_gross_usd=None, worldwide_gross_usd=100)) is None
    assert _check_domestic_exceeds_worldwide(_movie(domestic_gross_usd=100, worldwide_gross_usd=None)) is None


def test_flags_opening_weekend_exceeding_domestic_total():
    movie = _movie(domestic_gross_usd=10_000_000)
    week1 = WeeklyGrossObservation(weekend_gross_usd=15_000_000, week_number=1, territory="domestic", source="test")
    anomaly = _check_opening_weekend_exceeds_domestic_total(week1, movie)
    assert anomaly is not None
    assert anomaly.rule_name == "opening_weekend_exceeds_domestic_total"


def test_does_not_flag_normal_opening_weekend():
    movie = _movie(domestic_gross_usd=100_000_000)
    week1 = WeeklyGrossObservation(weekend_gross_usd=20_000_000, week_number=1, territory="domestic", source="test")
    assert _check_opening_weekend_exceeds_domestic_total(week1, movie) is None


def test_flags_too_short_runtime_with_real_gross():
    movie = _movie(runtime_minutes=25, domestic_gross_usd=1_000_000)
    anomaly = _check_implausible_runtime(movie)
    assert anomaly is not None
    assert anomaly.severity == "medium"


def test_flags_too_long_runtime():
    movie = _movie(runtime_minutes=300, domestic_gross_usd=1_000_000)
    anomaly = _check_implausible_runtime(movie)
    assert anomaly is not None
    assert anomaly.severity == "low"


def test_does_not_flag_runtime_without_real_gross_on_record():
    # an unreleased/no-data film with a short runtime isn't necessarily wrong - there's nothing
    # to contradict yet
    movie = _movie(runtime_minutes=25, domestic_gross_usd=None)
    assert _check_implausible_runtime(movie) is None


def test_flags_implausible_budget_for_wide_release():
    movie = _movie(budget_usd=5_000)
    week1 = WeeklyGrossObservation(theater_count=3000, week_number=1, territory="domestic", source="test")
    anomaly = _check_implausible_budget_for_wide_release(week1, movie)
    assert anomaly is not None
    assert anomaly.rule_name == "implausible_budget_for_wide_release"


def test_does_not_flag_small_budget_for_limited_release():
    movie = _movie(budget_usd=5_000)
    week1 = WeeklyGrossObservation(theater_count=10, week_number=1, territory="domestic", source="test")
    assert _check_implausible_budget_for_wide_release(week1, movie) is None


def test_genre_outlier_flags_movie_wildly_out_of_line_with_genre_peers():
    # 5 typical genre peers around a ~3x return (with a little real-world variance, so the
    # leave-one-out stdev isn't exactly zero), one outlier at ~300x - leave-one-out mean/stdev for
    # the outlier is computed only from the 5 typical peers, so it should stand out clearly
    typical_grosses = [28_000_000, 29_000_000, 30_000_000, 31_000_000, 32_000_000]
    typical = [
        _movie(id=i, tmdb_id=i, budget_usd=10_000_000, worldwide_gross_usd=gross, genres=["Drama"])
        for i, gross in enumerate(typical_grosses, start=1)
    ]
    outlier = _movie(id=6, tmdb_id=6, budget_usd=1_000_000, worldwide_gross_usd=300_000_000, genres=["Drama"])
    anomalies = _genre_budget_to_gross_outliers([*typical, outlier])
    flagged_ids = {a.movie.id for a in anomalies}
    assert 6 in flagged_ids
    assert 1 not in flagged_ids


def test_genre_outlier_skips_genres_below_minimum_sample():
    movies = [
        _movie(id=i, tmdb_id=i, budget_usd=10_000_000, worldwide_gross_usd=30_000_000, genres=["Horror"])
        for i in range(1, 4)
    ]
    assert _genre_budget_to_gross_outliers(movies) == []
