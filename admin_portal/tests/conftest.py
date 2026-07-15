import pytest

from app import create_app
from app.extensions import db
from app.models.admin_user import AdminUser, Role


@pytest.fixture()
def app():
    application = create_app("app.config.TestConfig")

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    with app.app_context():
        user = AdminUser(username="admin", email="admin@example.com", role=Role.SUPERADMIN)
        user.set_password("correct horse battery staple")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture()
def logged_in_client(client, admin_user):
    client.post(
        "/login",
        data={"username": "admin", "password": "correct horse battery staple"},
        follow_redirects=True,
    )
    return client
