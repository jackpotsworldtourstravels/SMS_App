import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models.admin_user import AdminUser, Role
from app.models.message import Message
from app.services.reference_extraction import extract_reference_id


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


@click.command("backfill-reference-ids")
@with_appcontext
def backfill_reference_ids() -> None:
    """One-off maintenance: re-run reference-ID extraction against messages
    stored before the reference_id column existed. Safe to re-run — only
    touches rows where reference_id is currently NULL."""

    messages = Message.query.filter(Message.reference_id.is_(None)).all()
    updated = 0

    for message in messages:
        reference_id = extract_reference_id(message.message_body)
        if reference_id:
            message.reference_id = reference_id
            updated += 1

    db.session.commit()
    click.echo(f"Scanned {len(messages)} message(s), updated {updated} with a reference_id.")
