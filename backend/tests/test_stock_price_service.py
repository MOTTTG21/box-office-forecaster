from datetime import date, datetime, timezone

import httpx

from app.services.stock_price_service import _fetch_weekly_closes


def _ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def _client_returning(payload: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="https://query1.finance.yahoo.com")


def _yahoo_payload(timestamps: list[int], closes: list[float | None]) -> dict:
    return {
        "chart": {
            "result": [
                {
                    "timestamp": timestamps,
                    "indicators": {"quote": [{"close": closes}]},
                }
            ]
        }
    }


def test_a_bar_dated_on_a_non_monday_is_normalized_to_that_isos_week_monday():
    # 2026-01-06 is a real Tuesday (a week shifted off Monday around a holiday, which is exactly
    # when Yahoo's weekly bar anchor drifts). Its ISO week's Monday is 2026-01-05.
    tuesday = date(2026, 1, 6)
    payload = _yahoo_payload([_ts(tuesday)], [106.55])

    with _client_returning(payload) as client:
        points = _fetch_weekly_closes(client, "DIS")

    assert points == [(date(2026, 1, 5), 106.55)]


def test_multiple_weeks_all_normalize_correctly():
    weeks = [date(2026, 1, 6), date(2026, 1, 12), date(2026, 1, 20)]
    payload = _yahoo_payload([_ts(d) for d in weeks], [100.0, 101.0, 99.5])

    with _client_returning(payload) as client:
        points = _fetch_weekly_closes(client, "DIS")

    assert [p[0] for p in points] == [date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 19)]


def test_a_null_close_is_skipped_not_treated_as_zero():
    weeks = [date(2026, 1, 6), date(2026, 1, 12)]
    payload = _yahoo_payload([_ts(d) for d in weeks], [None, 101.0])

    with _client_returning(payload) as client:
        points = _fetch_weekly_closes(client, "DIS")

    assert points == [(date(2026, 1, 12), 101.0)]


def test_no_result_rows_returns_empty_list():
    with _client_returning({"chart": {"result": []}}) as client:
        points = _fetch_weekly_closes(client, "NOTATICKER")

    assert points == []


def test_two_bars_normalizing_to_the_same_week_are_deduped_keeping_the_later_value():
    # Real observed Yahoo behavior: a completed bar plus a partial bar for the
    # current in-progress week, both landing in the same ISO week after normalization.
    same_week = [date(2026, 9, 7), date(2026, 9, 9)]
    payload = _yahoo_payload([_ts(d) for d in same_week], [28.0, 28.5])

    with _client_returning(payload) as client:
        points = _fetch_weekly_closes(client, "WBD")

    assert points == [(date(2026, 9, 7), 28.5)]
