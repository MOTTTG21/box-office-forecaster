from datetime import date, timedelta


def current_box_office_week(today: date) -> tuple[date, date]:
    """The box office week is Monday-Sunday (studios report official weekend numbers Sunday)."""
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday
