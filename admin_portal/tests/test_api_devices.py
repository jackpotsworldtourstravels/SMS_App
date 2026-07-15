import uuid

from app.extensions import db
from app.models.device import Device


def _register(client, device_id=None):
    device_id = device_id or str(uuid.uuid4())
    response = client.post(
        "/api/v1/register-device",
        json={
            "device_id": device_id,
            "device_name": "Test Phone",
            "manufacturer": "Xiaomi",
            "model": "23124RN87I",
            "android_version": "14",
            "app_version_name": "1.1",
            "app_version_code": 2,
        },
    )
    return response


def test_register_device_returns_token(client):
    response = _register(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data["device_id"]
    assert data["api_token"]
    assert data["heartbeat_interval_seconds"] > 0


def test_register_device_missing_fields_rejected(client):
    response = client.post("/api/v1/register-device", json={})
    assert response.status_code == 400


def test_reregister_rotates_token(client):
    device_id = str(uuid.uuid4())
    first = _register(client, device_id).get_json()
    second = _register(client, device_id).get_json()
    assert first["api_token"] != second["api_token"]
    assert first["device_id"] == second["device_id"]


def test_heartbeat_requires_token(client):
    response = client.post("/api/v1/heartbeat")
    assert response.status_code == 401


def test_heartbeat_marks_device_online(app, client):
    data = _register(client).get_json()
    response = client.post(
        "/api/v1/heartbeat",
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert response.status_code == 200
    with app.app_context():
        device = db.session.get(Device, data["device_id"])
        assert device.is_online is True


def test_revoked_device_cannot_authenticate(app, client):
    data = _register(client).get_json()
    with app.app_context():
        device = db.session.get(Device, data["device_id"])
        device.is_active = False
        db.session.commit()

    response = client.post(
        "/api/v1/heartbeat",
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert response.status_code == 401


def test_device_config_returns_bank_sender_ids(client):
    data = _register(client).get_json()
    response = client.get(
        "/api/v1/device-config",
        headers={"Authorization": f"Bearer {data['api_token']}"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "HDFCBK" in body["bank_sender_ids"]
