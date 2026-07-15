from datetime import datetime, time

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import select

from app.blueprints.audit import audit_bp
from app.models.admin_user import Role
from app.models.audit_log import AuditLog, EventType
from app.utils.query_helpers import paginate
from app.utils.rbac import roles_required


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


@audit_bp.route("/")
@login_required
@roles_required(Role.ADMIN)
def index():
    event_type = request.args.get("event_type", "")
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())

    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(date_to.date(), time.max))

    page = paginate(stmt)

    event_types = [
        getattr(EventType, name)
        for name in dir(EventType)
        if not name.startswith("_")
    ]

    return render_template(
        "audit/index.html",
        page=page,
        event_type=event_type,
        date_from=request.args.get("date_from", ""),
        date_to=request.args.get("date_to", ""),
        event_types=event_types,
    )
