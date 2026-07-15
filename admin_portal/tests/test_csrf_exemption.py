import uuid

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def csrf_enabled_client():
    """A client with CSRF protection genuinely active, unlike the default
    TestConfig (which disables CSRF globally and would silently mask a
    regression in the /api/v1 blueprint's CSRF exemption)."""

    application = create_app("app.config.TestConfig")
    application.config["WTF_CSRF_ENABLED"] = True

    with application.app_context():
        db.create_all()
        yield application.test_client()
        db.session.remove()
        db.drop_all()


def test_register_device_works_with_csrf_protection_active(csrf_enabled_client):
    # Regression test: /api/v1 is nested inside the /api blueprint, and
    # Flask-WTF's exemption check matches on the exact Blueprint object
    # bound to request.blueprint, which for a nested blueprint is the
    # child (api.v1's v1_bp), not the parent (api_bp) it's registered
    # under. Exempting only api_bp silently fails to exempt anything
    # inside it, and this device-facing POST endpoint (which never sends
    # a CSRF token, since it isn't a browser session) starts rejecting
    # every request with "The CSRF token is missing."
    response = csrf_enabled_client.post(
        "/api/v1/register-device",
        json={"device_id": str(uuid.uuid4()), "device_name": "CSRF Regression Test"},
    )
    assert response.status_code == 201
    assert "api_token" in response.get_json()
