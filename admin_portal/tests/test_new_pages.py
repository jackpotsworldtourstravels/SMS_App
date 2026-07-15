import uuid
from decimal import Decimal

from app.extensions import db
from app.models.device import Device
from app.models.end_user import EndUser
from app.models.message import Message, MessageCategory
from app.services.dashboard_stats import (
    get_average_processing_seconds,
    get_hourly_activity,
    get_top_banks,
    get_top_users,
    get_transactions_per_day,
)


def _seed(app):
    with app.app_context():
        device = Device(id=str(uuid.uuid4()), device_name="Redmi Note 12", api_token_hash="x", is_online=True)
        user = EndUser(name="Test User")
        db.session.add_all([device, user])
        db.session.flush()
        device.end_user_id = user.id

        credit = Message(
            device_id=device.id,
            end_user_id=user.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.1000 credited to A/c XX1234. Ref No 111122223333",
            category=MessageCategory.CREDIT,
            reference_id="111122223333",
            amount=Decimal("1000.00"),
            received_at=db.func.now(),
            uploaded_at=db.func.now(),
            client_message_id="txn-credit",
        )
        debit = Message(
            device_id=device.id,
            end_user_id=user.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.250 debited from A/c XX1234. Ref No 444455556666",
            category=MessageCategory.DEBIT,
            reference_id="444455556666",
            amount=Decimal("250.00"),
            received_at=db.func.now(),
            uploaded_at=db.func.now(),
            client_message_id="txn-debit",
        )
        otp = Message(
            device_id=device.id,
            end_user_id=user.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="123456 is your OTP.",
            category=MessageCategory.OTP,
            received_at=db.func.now(),
            uploaded_at=db.func.now(),
            client_message_id="txn-otp",
        )
        db.session.add_all([credit, debit, otp])
        db.session.commit()
        return device.id, user.id


def test_transactions_page_shows_only_credit_and_debit(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/transactions/")
    assert response.status_code == 200
    assert b"111122223333" in response.data
    assert b"444455556666" in response.data
    assert b"OTP" not in response.data


def test_transactions_page_filter_by_type(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/transactions/?type=CREDIT")
    assert b"111122223333" in response.data
    assert b"444455556666" not in response.data


def test_transactions_page_filter_by_bank(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/transactions/?bank=HDFCBK")
    assert b"111122223333" in response.data
    response = logged_in_client.get("/transactions/?bank=NOPE")
    assert b"111122223333" not in response.data


def test_analytics_page_renders(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/analytics/")
    assert response.status_code == 200
    assert b"Analytics" in response.data
    assert b"Top Banks" in response.data


def test_settings_page_renders(app, logged_in_client):
    response = logged_in_client.get("/settings/")
    assert response.status_code == 200
    assert b"Settings" in response.data


def test_dashboard_stats_aggregations(app):
    _seed(app)
    with app.app_context():
        assert get_average_processing_seconds() is not None
        assert get_average_processing_seconds() >= 0

        hourly = get_hourly_activity()
        assert len(hourly) == 24
        assert sum(row["count"] for row in hourly) == 3

        banks = get_top_banks()
        assert banks[0]["bank"] == "HDFCBK"
        assert banks[0]["count"] == 2

        users = get_top_users()
        assert users[0]["user"] == "Test User"
        assert users[0]["count"] == 3

        per_day = get_transactions_per_day()
        categories = {row["category"] for row in per_day}
        assert categories == {"CREDIT", "DEBIT"}


def test_dashboard_stats_new_fields_present(app):
    _seed(app)
    with app.app_context():
        from app.services.dashboard_stats import get_dashboard_stats

        stats = get_dashboard_stats()
        assert stats["transactions_today"] == 2
        assert stats["messages_unknown"] == 0
        assert stats["avg_processing_seconds"] is not None
