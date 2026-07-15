from app.models.audit_log import AuditLog, EventType


def test_login_success_redirects_to_dashboard(client, admin_user):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "correct horse battery staple"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_login_failure_shows_error(client, admin_user):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong password"},
        follow_redirects=True,
    )
    assert b"Invalid username or password" in response.data


def test_login_writes_audit_log(app, client, admin_user):
    client.post(
        "/login",
        data={"username": "admin", "password": "correct horse battery staple"},
    )
    with app.app_context():
        entry = AuditLog.query.filter_by(event_type=EventType.LOGIN).first()
        assert entry is not None
        assert entry.actor_label == "admin"


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_writes_audit_log(app, logged_in_client):
    logged_in_client.post("/logout")
    with app.app_context():
        entry = AuditLog.query.filter_by(event_type=EventType.LOGOUT).first()
        assert entry is not None
