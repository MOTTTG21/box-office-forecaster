from datetime import datetime, timezone

from app.models import BacktestPrediction
from app.services.backtest_report_service import get_backtest_report


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, _model):
        return _FakeQuery(self._rows)


def _row(*, comp_method="director", release_year=2024, pct_error=10.0):
    return BacktestPrediction(
        title="Test Movie",
        release_year=release_year,
        budget_usd=100_000_000,
        actual_opening_weekend_usd=50_000_000,
        predicted_opening_weekend_usd=55_000_000,
        computed_at=datetime.now(timezone.utc),  # a real Session would fill this via server_default
        pct_error=pct_error,
        comp_method=comp_method,
    )


def test_no_rows_returns_an_honest_empty_report():
    report = get_backtest_report(_FakeSession([]))

    assert report.sample_count == 0
    assert report.overall_median_abs_pct_error is None
    assert report.by_comp_method == []
    assert report.by_release_year == []


def test_overall_median_uses_absolute_error():
    rows = [
        _row(pct_error=-40.0),
        _row(pct_error=10.0),
        _row(pct_error=20.0),
        _row(pct_error=30.0),
        _row(pct_error=5.0),
    ]

    report = get_backtest_report(_FakeSession(rows))

    assert report.sample_count == 5
    assert report.overall_median_abs_pct_error == 20.0


def test_groups_below_min_size_are_excluded():
    # 4 director rows (below MIN_GROUP_SIZE=5), 5 genre rows
    rows = [_row(comp_method="director") for _ in range(4)] + [_row(comp_method="genre") for _ in range(5)]

    report = get_backtest_report(_FakeSession(rows))

    labels = [g.label for g in report.by_comp_method]
    assert "genre" in labels
    assert "director" not in labels


def test_breaks_down_by_release_year():
    rows = [_row(release_year=2023) for _ in range(5)] + [_row(release_year=2024) for _ in range(6)]

    report = get_backtest_report(_FakeSession(rows))

    labels = {g.label: g.sample_count for g in report.by_release_year}
    assert labels == {"2023": 5, "2024": 6}


def test_a_missing_release_year_is_labeled_unknown_not_dropped():
    rows = [_row(release_year=None) for _ in range(5)]

    report = get_backtest_report(_FakeSession(rows))

    assert report.by_release_year[0].label == "unknown"
    assert report.by_release_year[0].sample_count == 5
