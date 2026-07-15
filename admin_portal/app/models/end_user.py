from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EndUserStatus:
    ACTIVE = "active"
    DISABLED = "disabled"


class EndUser(db.Model):
    __tablename__ = "end_user"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(120), nullable=False)
    phone_number: str | None = db.Column(db.String(20))
    notes: str | None = db.Column(db.Text)
    status: str = db.Column(
        db.String(20), nullable=False, default=EndUserStatus.ACTIVE, index=True
    )

    created_by_admin_id: int | None = db.Column(
        db.Integer, db.ForeignKey("admin_user.id")
    )

    created_at: datetime = db.Column(
        db.DateTime(timezone=True), default=_utcnow, index=True
    )
    updated_at: datetime = db.Column(
        db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    devices = db.relationship("Device", back_populates="end_user")
    messages = db.relationship(
        "Message", back_populates="end_user", lazy="dynamic"
    )

    @property
    def is_active(self) -> bool:
        return self.status == EndUserStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<EndUser {self.id} name={self.name!r}>"
