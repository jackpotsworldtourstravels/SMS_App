import uuid

from app.extensions import db
from app.models.device import Device
from app.models.message import Message


def _register(client):
    device_id = str(uuid.uuid4())
    response = client.post(
        "/api/v1/register-device",
        json={"device_id": device_id, "device_name": "Test Phone"},
    )
    return response.get_json()


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_upload_message_categorizes_and_stores(app, client):
    reg = _register(client)
    response = client.post(
        "/api/v1/messages",
        headers=_auth_header(reg["api_token"]),
        json={
            "messages": [
                {
                    "client_message_id": "m1",
                    "sender_raw": "AX-HDFCBK-S",
                    "sender_matched": "HDFCBK",
                    "body": "Rs.500.00 debited from A/c XX1234. Ref No 445566778899. Avl bal Rs.10,234.50",
                    "received_at": "2026-07-14T10:00:00Z",
                }
            ]
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["accepted"] == 1
    assert body["results"][0]["category"] == "DEBIT"
    assert body["results"][0]["reference_id"] == "445566778899"

    with app.app_context():
        message = Message.query.filter_by(client_message_id="m1").first()
        assert message is not None
        assert message.category == "DEBIT"
        assert message.message_body.startswith("Rs.500.00")
        assert message.reference_id == "445566778899"


def test_duplicate_message_is_deduped(client):
    reg = _register(client)
    payload = {
        "messages": [
            {
                "client_message_id": "dup-1",
                "sender_raw": "AX-HDFCBK-S",
                "sender_matched": "HDFCBK",
                "body": "Test OTP 123456",
                "received_at": "2026-07-14T10:00:00Z",
            }
        ]
    }
    first = client.post(
        "/api/v1/messages", headers=_auth_header(reg["api_token"]), json=payload
    ).get_json()
    second = client.post(
        "/api/v1/messages", headers=_auth_header(reg["api_token"]), json=payload
    ).get_json()

    assert first["accepted"] == 1
    assert second["accepted"] == 0
    assert second["duplicates"] == 1


def test_messages_require_token(client):
    response = client.post("/api/v1/messages", json={"messages": []})
    assert response.status_code == 401


def test_revoked_device_cannot_upload_messages(app, client):
    reg = _register(client)
    with app.app_context():
        device = db.session.get(Device, reg["device_id"])
        device.is_active = False
        db.session.commit()

    response = client.post(
        "/api/v1/messages",
        headers=_auth_header(reg["api_token"]),
        json={
            "messages": [
                {
                    "client_message_id": "should-fail",
                    "sender_raw": "AX-HDFCBK-S",
                    "sender_matched": "HDFCBK",
                    "body": "test",
                    "received_at": "2026-07-14T10:00:00Z",
                }
            ]
        },
    )
    assert response.status_code == 401

    with app.app_context():
        assert Message.query.filter_by(client_message_id="should-fail").first() is None
