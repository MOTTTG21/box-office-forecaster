from app.services.prediction_service import _budget_scaled_average


def test_scales_comp_by_budget_ratio():
    # comp made $10M on a $5M budget; target has a $20M budget -> scaled estimate $40M
    rows = [(10_000_000, 5_000_000)]
    assert _budget_scaled_average(rows, target_budget_usd=20_000_000) == 40_000_000


def test_averages_multiple_scaled_comps():
    rows = [(10_000_000, 5_000_000), (30_000_000, 10_000_000)]
    # scaled: 10M*(20M/5M)=40M, 30M*(20M/10M)=60M -> average 50M
    assert _budget_scaled_average(rows, target_budget_usd=20_000_000) == 50_000_000


def test_drops_comp_missing_budget_when_target_budget_known():
    # real bug this guards against: "By Any Means" ($30M budget) had a comp with no budget
    # on record and a tiny $65,942 raw opening - including it raw produced a nonsense estimate
    rows = [(65_942, None), (20_000_000, 10_000_000)]
    assert _budget_scaled_average(rows, target_budget_usd=30_000_000) == 60_000_000


def test_returns_none_when_target_budget_unknown():
    # real bug this guards against: a 50-minute TV special with no budget got a $100M+
    # "prediction" from raw genre-mate blending before this rule was added
    rows = [(100_000_000, 150_000_000), (50_000_000, 80_000_000)]
    assert _budget_scaled_average(rows, target_budget_usd=None) is None


def test_returns_none_with_no_usable_comps():
    rows = [(1_000_000, None), (2_000_000, None)]
    assert _budget_scaled_average(rows, target_budget_usd=30_000_000) is None


def test_returns_none_with_no_rows():
    assert _budget_scaled_average([], target_budget_usd=30_000_000) is None


def test_skips_rows_with_missing_weekend_gross():
    rows = [(None, 10_000_000), (20_000_000, 10_000_000)]
    assert _budget_scaled_average(rows, target_budget_usd=10_000_000) == 20_000_000
