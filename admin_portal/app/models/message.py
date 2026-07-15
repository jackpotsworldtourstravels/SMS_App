from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessageCategory:
    OTP = "OTP"
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    UNKNOWN = "UNKNOWN"

    ALL = (OTP, CREDIT, DEBIT, UNKNOWN)


class Message(db.Model):
    __tablename__ = "message"

    # BigInteger on Postgres; SQLite's autoincrement rowid aliasing only
    # works on plain INTEGER primary keys, so fall back to that on SQLite
    # (used in tests) via with_variant.
    id: int = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    device_id: str = db.Column(
        db.String(36), db.ForeignKey("device.id"), nullable=False, index=True
    )
    device = db.relationship("Device", back_populates="messages")

    end_user_id: int | None = db.Column(
        db.Integer, db.ForeignKey("end_user.id"), index=True
    )
    end_user = db.relationship("EndUser", back_populates="messages")

    sender_raw: str = db.Column(db.String(32), nullable=False)
    sender_matched: str = db.Column(db.String(32), nullable=False)
    message_body: str = db.Column(db.Text, nullable=False)

    category: str = db.Column(
        db.String(10), nullable=False, default=MessageCategory.UNKNOWN, index=True
    )

    received_at: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, index=True
    )
    uploaded_at: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )

    client_message_id: str = db.Column(db.String(64), nullable=False)

    created_at: datetime = db.Column(db.DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "device_id", "client_message_id", name="uq_message_device_client_id"
        ),
        db.Index("ix_message_device_received", "device_id", "received_at"),
        db.Index("ix_message_category_received", "category", "received_at"),
        db.Index("ix_message_enduser_received", "end_user_id", "received_at"),
    )

    def __repr__(self) -> str:
        return f"<Message {self.id} category={self.category!r} device={self.device_id}>"
