from datetime import datetime, timezone

import bcrypt
from flask_login import UserMixin

from app.extensions import db


class Role:
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    VIEWER = "viewer"

    ORDER = {SUPERADMIN: 3, ADMIN: 2, VIEWER: 1}

    @classmethod
    def at_least(cls, role: str, minimum: str) -> bool:
        return cls.ORDER.get(role, 0) >= cls.ORDER.get(minimum, 0)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_user"

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email: str = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(255), nullable=False)
    role: str = db.Column(db.String(20), nullable=False, default=Role.ADMIN)
    is_active_flag: bool = db.Column(
        "is_active", db.Boolean, nullable=False, default=True
    )
    created_at: datetime = db.Column(db.DateTime(timezone=True), default=_utcnow)
    last_login_at: datetime | None = db.Column(db.DateTime(timezone=True))

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def has_role_at_least(self, minimum_role: str) -> bool:
        return Role.at_least(self.role, minimum_role)

    # Flask-Login's UserMixin already provides is_authenticated/is_anonymous/
    # get_id; override is_active to respect our own soft-disable flag.
    @property
    def is_active(self) -> bool:
        return self.is_active_flag

    def __repr__(self) -> str:
        return f"<AdminUser {self.username!r} role={self.role!r}>"
