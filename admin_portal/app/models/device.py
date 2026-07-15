import uuid
from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Device(db.Model):
    __tablename__ = "device"

    # Client-generated UUIDv4, stored as text so the schema works
    # identically on Postgres (prod) and SQLite (tests) without a
    # dialect-specific UUID column type.
    id: str = db.Column(db.String(36), primary_key=True, default=_new_uuid)

    device_name: str | None = db.Column(db.String(120))
    manufacturer: str | None = db.Column(db.String(80))
    model: str | None = db.Column(db.String(80))
    android_version: str | None = db.Column(db.String(20))
    app_version_name: str | None = db.Column(db.String(20))
    app_version_code: int | None = db.Column(db.Integer)

    api_token_hash: str = db.Column(db.String(128), nullable=False, index=True)
    token_created_at: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow
    )
    token_revoked_at: datetime | None = db.Column(db.DateTime(timezone=True))

    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)

    registered_at: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
    last_seen_at: datetime | None = db.Column(db.DateTime(timezone=True), index=True)
    is_online: bool = db.Column(
        db.Boolean, nullable=False, default=False, index=True
    )

    end_user_id: int | None = db.Column(
        db.Integer, db.ForeignKey("end_user.id"), index=True
    )
    end_user = db.relationship("EndUser", back_populates="devices")

    created_at: datetime = db.Column(db.DateTime(timezone=True), default=_utcnow)
    updated_at: datetime = db.Column(
        db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    messages = db.relationship(
        "Message", back_populates="device", lazy="dynamic"
    )

    def is_token_valid(self) -> bool:
        return self.is_active and self.token_revoked_at is None

    def __repr__(self) -> str:
        return f"<Device {self.id} name={self.device_name!r}>"
