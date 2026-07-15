from datetime import datetime, timezone

from sqlalchemy import JSON

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventType:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DEVICE_REGISTER = "DEVICE_REGISTER"
    DEVICE_REVOKED = "DEVICE_REVOKED"
    DEVICE_DISCONNECT = "DEVICE_DISCONNECT"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    MESSAGE_UPLOAD = "MESSAGE_UPLOAD"
    SETTINGS_CHANGE = "SETTINGS_CHANGE"


class ActorType:
    ADMIN_USER = "admin_user"
    DEVICE = "device"
    SYSTEM = "system"


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    # BigInteger on Postgres; SQLite's autoincrement rowid aliasing only
    # works on plain INTEGER primary keys, so fall back to that on SQLite
    # (used in tests) via with_variant.
    id: int = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    event_type: str = db.Column(db.String(40), nullable=False, index=True)
    actor_type: str = db.Column(db.String(20), nullable=False)
    actor_id: str | None = db.Column(db.String(64))
    actor_label: str | None = db.Column(db.String(120))

    target_type: str | None = db.Column(db.String(40))
    target_id: str | None = db.Column(db.String(64))

    description: str = db.Column(db.String(255), nullable=False)
    ip_address: str | None = db.Column(db.String(45))
    meta: dict | None = db.Column(JSON)

    created_at: datetime = db.Column(
        db.DateTime(timezone=True), default=_utcnow, index=True
    )

    __table_args__ = (
        db.Index("ix_audit_event_created", "event_type", "created_at"),
        db.Index("ix_audit_actor_created", "actor_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} {self.event_type} {self.description!r}>"
