"""Reads the cached backtest_predictions table (written by `python -m app.ml.evaluate --save`,
never computed live - see app/models/backtest_prediction.py for why) and breaks the model's real
error down by comp-selection method (director-comp vs genre-fallback) and by release year, so a
real question - "does this heuristic's accuracy actually hold up over time, or lean on one
comp tier more than the other" - has a real, checkable answer instead of a single blended number.

A group with fewer than MIN_GROUP_SIZE rows is left out of its breakdown, same "not enough data"
rule used everywhere else in this app - a median from 2 movies isn't a trend.
"""

import statistics
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import BacktestPrediction
from app.schemas.data_quality import BacktestReport, ErrorByGroup

MIN_GROUP_SIZE = 5


def _median_abs_error(rows: list[BacktestPrediction]) -> float:
    return statistics.median(abs(r.pct_error) for r in rows)


def _grouped(rows: list[BacktestPrediction], key) -> list[ErrorByGroup]:
    groups: dict[str, list[BacktestPrediction]] = defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)

    return sorted(
        (
            ErrorByGroup(label=label, sample_count=len(group), median_abs_pct_error=round(_median_abs_error(group), 1))
            for label, group in groups.items()
            if len(group) >= MIN_GROUP_SIZE
        ),
        key=lambda g: g.label,
    )


def get_backtest_report(db: Session) -> BacktestReport:
    rows = db.query(BacktestPrediction).all()

    if not rows:
        return BacktestReport(sample_count=0, by_comp_method=[], by_release_year=[])

    return BacktestReport(
        computed_at=max(r.computed_at for r in rows),
        sample_count=len(rows),
        overall_median_abs_pct_error=round(_median_abs_error(rows), 1),
        by_comp_method=_grouped(rows, lambda r: r.comp_method),
        by_release_year=_grouped(rows, lambda r: str(r.release_year) if r.release_year else "unknown"),
    )
