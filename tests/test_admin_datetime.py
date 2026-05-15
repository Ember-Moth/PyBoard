"""Admin UI time formatting helpers."""

from app.admin_ui.deps import datetime_input_value, datetime_or_none, format_datetime
from app.admin_ui.forms import coupon_create_from_form, user_update_from_form


def test_datetime_input_round_trip() -> None:
    timestamp = datetime_or_none("2026-05-15T09:30")

    assert timestamp is not None
    assert datetime_input_value(timestamp) == "2026-05-15T09:30"
    assert format_datetime(timestamp) == "2026-05-15 09:30:00"


def test_datetime_filter_handles_empty_and_existing_text() -> None:
    assert format_datetime(0) == "-"
    assert format_datetime(None) == "-"
    assert format_datetime("2026-05-14 00:00:00") == "2026-05-14 00:00:00"


def test_user_form_preserves_original_expired_at_when_datetime_is_empty() -> None:
    data = user_update_from_form({"expired_at": "", "expired_at_original": "0"})

    assert data.expired_at == 0


def test_coupon_form_accepts_datetime_local_values() -> None:
    data = coupon_create_from_form(
        {
            "name": "Spring",
            "type": "1",
            "value": "100",
            "started_at": "2026-05-15T09:30",
            "ended_at": "2026-05-16T09:30",
        }
    )

    assert data.started_at == datetime_or_none("2026-05-15T09:30")
    assert data.ended_at == datetime_or_none("2026-05-16T09:30")
