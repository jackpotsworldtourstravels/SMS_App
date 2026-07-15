import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models.admin_user import AdminUser, Role


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
)
@click.option(
    "--role",
    type=click.Choice([Role.SUPERADMIN, Role.ADMIN, Role.VIEWER]),
    default=Role.SUPERADMIN,
)
@with_appcontext
def create_admin(username: str, email: str, password: str, role: str) -> None:
    """Create a portal login. This is the only way to provision AdminUser
    accounts in v1 — there is no self-service signup/reset UI."""

    if AdminUser.query.filter_by(username=username).first():
        click.echo(f"Error: username '{username}' already exists.", err=True)
        raise SystemExit(1)

    if AdminUser.query.filter_by(email=email).first():
        click.echo(f"Error: email '{email}' already exists.", err=True)
        raise SystemExit(1)

    user = AdminUser(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    click.echo(f"Created {role} user '{username}' ({email}).")
