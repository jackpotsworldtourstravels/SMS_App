import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models.admin_user import AdminUser, Role
from app.models.device import Device
from app.models.message import Message
from app.services.reference_extraction import extract_reference_id

# Test/dummy records created during development and Render deploy
# verification — never real device or transaction data.
_DUMMY_DEVICE_IDS = (
    "3b367883-29c3-4465-9130-c12eab007f84",  # "Reference ID verify"
    "99999999-9999-9999-9999-999999999999",  # "Render Deploy Test"
)
_STRAY_MESSAGE_DEVICE_ID = "10f52fd6-17d6-47bf-9b0a-849a3f32e897"  # real "vivo I2217" device
_STRAY_MESSAGE_SENDER_RAW = "VM-BOBSMS-S"
_STRAY_MESSAGE_CATEGORY = "UNKNOWN"


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


@click.command("cleanup-test-records")
@with_appcontext
def cleanup_test_records() -> None:
    """One-off maintenance: remove known test/dummy devices and messages
    created during development and Render deploy verification. Safe to
    re-run — every deletion is keyed by exact ID, so once removed there is
    nothing left to match."""

    deleted_messages = Message.query.filter(
        Message.device_id.in_(_DUMMY_DEVICE_IDS)
    ).delete(synchronize_session=False)

    deleted_stray = Message.query.filter(
        Message.device_id == _STRAY_MESSAGE_DEVICE_ID,
        Message.sender_raw == _STRAY_MESSAGE_SENDER_RAW,
        Message.category == _STRAY_MESSAGE_CATEGORY,
        Message.reference_id.is_(None),
    ).delete(synchronize_session=False)

    deleted_devices = Device.query.filter(
        Device.id.in_(_DUMMY_DEVICE_IDS)
    ).delete(synchronize_session=False)

    db.session.commit()
    click.echo(
        f"Deleted {deleted_messages} dummy-device message(s), "
        f"{deleted_stray} stray message(s), "
        f"{deleted_devices} dummy device(s)."
    )
