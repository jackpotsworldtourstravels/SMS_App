from app.extensions import db
from app.models.admin_user import AdminUser, Role


def test_set_admin_password_updates_existing_user(app, admin_user):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["set-admin-password", "--username", "admin", "--password", "NewPass123"],
        input="NewPass123\n",
    )
    assert result.exit_code == 0
    assert "Password updated for user 'admin'." in result.output

    with app.app_context():
        user = db.session.get(AdminUser, admin_user)
        assert user.check_password("NewPass123")
        assert not user.check_password("correct horse battery staple")


def test_set_admin_password_unknown_username_fails(app):
    with app.app_context():
        assert AdminUser.query.filter_by(username="ghost").first() is None

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["set-admin-password", "--username", "ghost", "--password", "NewPass123"],
        input="NewPass123\n",
    )
    assert result.exit_code != 0
