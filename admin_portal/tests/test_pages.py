import uuid

from app.extensions import db
from app.models.device import Device
from app.models.end_user import EndUser
from app.models.message import Message, MessageCategory


def _seed(app):
    with app.app_context():
        device = Device(
            id=str(uuid.uuid4()),
            device_name="Redmi Note 12",
            api_token_hash="x",
            is_online=True,
        )
        user = EndUser(name="Test User")
        db.session.add_all([device, user])
        db.session.flush()
        device.end_user_id = user.id

        message = Message(
            device_id=device.id,
            end_user_id=user.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.500.00 debited from A/c XX1234. This is a full, untruncated body of decent length to check rendering.",
            category=MessageCategory.DEBIT,
            received_at=db.func.now(),
            client_message_id="seed-1",
        )
        db.session.add(message)
        db.session.commit()
        return device.id, user.id


def test_dashboard_renders_stats(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Connected (Online)" in response.data


def test_dashboard_api_json(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.get_json()
    assert data["totals"]["devices_total"] == 1
    assert data["totals"]["messages_debit"] == 1


def test_devices_page_shows_seeded_device(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/devices/")
    assert b"Redmi Note 12" in response.data
    assert b"Online" in response.data


def test_devices_page_filter_online(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/devices/?status=offline")
    assert b"Redmi Note 12" not in response.data


def test_messages_page_shows_full_body_untruncated(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/messages/")
    assert b"full, untruncated body of decent length" in response.data
    assert b"DEBIT" in response.data


def test_messages_page_category_filter(app, logged_in_client):
    _seed(app)
    response = logged_in_client.get("/messages/?category=OTP")
    assert b"full, untruncated body" not in response.data


def test_device_detail_and_revoke(app, logged_in_client):
    device_id, _ = _seed(app)
    response = logged_in_client.get(f"/devices/{device_id}")
    assert response.status_code == 200
    assert b"Revoke Device" in response.data

    logged_in_client.post(f"/devices/{device_id}/revoke", follow_redirects=True)

    with app.app_context():
        device = db.session.get(Device, device_id)
        assert device.is_active is False
        assert device.is_online is False


def test_audit_log_page_requires_admin_role(app, client, admin_user):
    from app.models.admin_user import AdminUser, Role

    with app.app_context():
        viewer = AdminUser(username="viewer", email="viewer@example.com", role=Role.VIEWER)
        viewer.set_password("viewer password 123")
        db.session.add(viewer)
        db.session.commit()

    client.post("/login", data={"username": "viewer", "password": "viewer password 123"})
    response = client.get("/audit/")
    assert response.status_code == 403


def test_audit_log_page_shows_entries(app, logged_in_client):
    _seed(app)
    logged_in_client.get(f"/devices/")  # no-op, just ensures session alive
    response = logged_in_client.get("/audit/")
    assert response.status_code == 200
