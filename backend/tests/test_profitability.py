from app.services.profitability import compute_profitability_status


def test_bomb_when_worldwide_gross_below_budget():
    assert compute_profitability_status(budget_usd=100_000_000, worldwide_gross_usd=50_000_000) == "bomb"


def test_flop_when_gross_recoups_budget_but_under_2_5x():
    # Real case from this project's own data: Dune (2021) at 2.49x budget
    assert compute_profitability_status(budget_usd=165_000_000, worldwide_gross_usd=410_668_500) == "flop"


def test_success_at_exactly_the_2_5x_threshold():
    assert compute_profitability_status(budget_usd=100_000_000, worldwide_gross_usd=250_000_000) == "success"


def test_success_well_above_threshold():
    # Real case: Oppenheimer at ~9.76x budget
    assert compute_profitability_status(budget_usd=100_000_000, worldwide_gross_usd=975_811_333) == "success"


def test_none_when_budget_missing():
    assert compute_profitability_status(budget_usd=None, worldwide_gross_usd=100_000_000) is None


def test_none_when_budget_zero():
    assert compute_profitability_status(budget_usd=0, worldwide_gross_usd=100_000_000) is None


def test_none_when_worldwide_gross_missing():
    assert compute_profitability_status(budget_usd=100_000_000, worldwide_gross_usd=None) is None


def test_boundary_just_under_1x_is_bomb_not_flop():
    assert compute_profitability_status(budget_usd=100_000_000, worldwide_gross_usd=99_999_999) == "bomb"


def test_boundary_exactly_1x_is_flop_not_bomb():
    assert compute_profitability_status(budget_usd=100_000_000, worldwide_gross_usd=100_000_000) == "flop"
