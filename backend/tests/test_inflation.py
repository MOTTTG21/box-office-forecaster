from app.services.inflation import CPI_ANNUAL_AVERAGE, LATEST_CPI_YEAR, adjust_for_inflation


def test_adjusts_known_year_to_latest_cpi_year():
    # $1 in 1972 (CPI 41.8) -> latest year CPI / 41.8
    expected = round(1 * CPI_ANNUAL_AVERAGE[LATEST_CPI_YEAR] / CPI_ANNUAL_AVERAGE[1972])
    assert adjust_for_inflation(1, 1972) == expected


def test_scales_a_real_budget_figure():
    # Jaws (1975), $9M budget - sanity check the ratio is a multi-x increase, not a rounding artifact
    result = adjust_for_inflation(9_000_000, 1975)
    assert result is not None
    assert result > 9_000_000 * 5


def test_returns_none_for_missing_amount():
    assert adjust_for_inflation(None, 1975) is None


def test_returns_none_for_missing_year():
    assert adjust_for_inflation(9_000_000, None) is None


def test_returns_none_for_year_outside_table():
    assert adjust_for_inflation(9_000_000, 1900) is None
    assert adjust_for_inflation(9_000_000, 2999) is None


def test_latest_year_is_a_noop():
    assert adjust_for_inflation(100, LATEST_CPI_YEAR) == 100
