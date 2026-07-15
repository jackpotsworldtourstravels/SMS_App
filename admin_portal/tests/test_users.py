import uuid

from app.extensions import db
from app.models.device import Device
from app.models.end_user import EndUser, EndUserStatus


def _make_device(app, device_id=None):
    with app.app_context():
        device = Device(
            id=device_id or str(uuid.uuid4()),
            device_name="Redmi Note 12",
            api_token_hash="x",
        )
        db.session.add(device)
        db.session.commit()
        return device.id


def test_users_index_requires_login(client):
    response = client.get("/users/")
    assert response.status_code == 302


def test_create_user_links_device(app, logged_in_client):
    device_id = _make_device(app)

    response = logged_in_client.post(
        "/users/new",
        data={"name": "Ramesh Kumar", "phone_number": "9876543210", "device_id": device_id, "notes": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"created" in response.data.lower()

    with app.app_context():
        user = EndUser.query.filter_by(name="Ramesh Kumar").first()
        assert user is not None
        device = db.session.get(Device, device_id)
        assert device.end_user_id == user.id


def test_edit_user_reassigns_device(app, logged_in_client):
    device_a = _make_device(app)
    device_b = _make_device(app)

    logged_in_client.post(
        "/users/new",
        data={"name": "Priya", "phone_number": "", "device_id": device_a, "notes": ""},
    )

    with app.app_context():
        user = EndUser.query.filter_by(name="Priya").first()
        user_id = user.id

    logged_in_client.post(
        f"/users/{user_id}/edit",
        data={"name": "Priya", "phone_number": "", "device_id": device_b, "notes": ""},
    )

    with app.app_context():
        da = db.session.get(Device, device_a)
        db_ = db.session.get(Device, device_b)
        assert da.end_user_id is None
        assert db_.end_user_id == user_id


def test_disable_user(app, logged_in_client):
    device_id = _make_device(app)
    logged_in_client.post(
        "/users/new",
        data={"name": "Anita", "phone_number": "", "device_id": device_id, "notes": ""},
    )
    with app.app_context():
        user = EndUser.query.filter_by(name="Anita").first()
        user_id = user.id

    logged_in_client.post(f"/users/{user_id}/disable", follow_redirects=True)

    with app.app_context():
        user = db.session.get(EndUser, user_id)
        assert user.status == EndUserStatus.DISABLED


def test_users_search(app, logged_in_client):
    device_id = _make_device(app)
    logged_in_client.post(
        "/users/new",
        data={"name": "Suresh Babu", "phone_number": "", "device_id": device_id, "notes": ""},
    )

    response = logged_in_client.get("/users/?q=Suresh")
    assert b"Suresh Babu" in response.data

    response = logged_in_client.get("/users/?q=NoSuchName")
    assert b"Suresh Babu" not in response.data
