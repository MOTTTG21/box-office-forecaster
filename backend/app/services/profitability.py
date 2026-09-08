PROFIT_MULTIPLE_FOR_SUCCESS = 2.5


def compute_profitability_status(budget_usd: int | None, worldwide_gross_usd: int | None) -> str | None:
    """Bomb / flop / success, using the industry rule of thumb that a film needs to gross
    roughly 2.5x its budget worldwide to be profitable once marketing and the
    theater's box-office split are accounted for. None if we don't have enough data.
    """
    if not budget_usd or worldwide_gross_usd is None:
        return None

    multiple = worldwide_gross_usd / budget_usd
    if multiple < 1.0:
        return "bomb"
    if multiple < PROFIT_MULTIPLE_FOR_SUCCESS:
        return "flop"
    return "success"
