from flask import has_request_context, request

from app.extensions import db
from app.models.audit_log import ActorType, AuditLog


def log_event(
    event_type: str,
    description: str,
    actor_type: str = ActorType.SYSTEM,
    actor_id: str | None = None,
    actor_label: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    meta: dict | None = None,
) -> AuditLog:
    """Write one audit trail row. Callers are responsible for db.session.commit()
    (usually as part of the same transaction as the change being audited)."""

    ip_address = None
    if has_request_context():
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

    entry = AuditLog(
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_label=actor_label,
        target_type=target_type,
        target_id=target_id,
        description=description,
        ip_address=ip_address,
        meta=meta,
    )
    db.session.add(entry)
    return entry
