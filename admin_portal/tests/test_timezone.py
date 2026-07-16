from datetime import datetime, timezone

from app.utils.timezone import to_ist


def test_to_ist_applies_five_thirty_offset():
    utc_dt = datetime(2026, 7, 15, 9, 5, 0, tzinfo=timezone.utc)
    ist_dt = to_ist(utc_dt)
    assert ist_dt.hour == 14
    assert ist_dt.minute == 35
    assert ist_dt.utcoffset().total_seconds() == 5.5 * 3600


def test_to_ist_treats_naive_datetime_as_utc():
    naive_dt = datetime(2026, 7, 15, 9, 5, 0)
    ist_dt = to_ist(naive_dt)
    assert ist_dt.hour == 14
    assert ist_dt.minute == 35


def test_to_ist_none_returns_none():
    assert to_ist(None) is None


def test_ist_jinja_filter_formats_12_hour_with_am_pm(app):
    with app.test_request_context():
        render = app.jinja_env.filters["ist"]
        utc_dt = datetime(2026, 7, 15, 9, 5, 0, tzinfo=timezone.utc)
        assert render(utc_dt) == "15 Jul 2026, 02:35 PM"
        assert render(None) == "—"


def test_ist_jinja_filter_accepts_custom_format(app):
    with app.test_request_context():
        render = app.jinja_env.filters["ist"]
        utc_dt = datetime(2026, 7, 15, 9, 5, 0, tzinfo=timezone.utc)
        assert render(utc_dt, "%d %b %Y") == "15 Jul 2026"
