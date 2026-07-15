from datetime import datetime, timezone

from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.blueprints.devices import devices_bp
from app.extensions import db
from app.models.admin_user import Role
from app.models.audit_log import ActorType, EventType
from app.models.device import Device
from app.services.audit import log_event
from app.utils.query_helpers import apply_search, apply_sort, paginate
from app.utils.rbac import roles_required


@devices_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    sort_key = request.args.get("sort", "registered_at")
    direction = request.args.get("dir", "desc")

    stmt = select(Device)

    if status_filter == "online":
        stmt = stmt.where(Device.is_online.is_(True))
    elif status_filter == "offline":
        stmt = stmt.where(Device.is_online.is_(False))

    stmt = apply_search(
        stmt,
        [Device.device_name, Device.id, Device.model, Device.manufacturer],
        q,
    )

    sort_map = {
        "device_name": Device.device_name,
        "registered_at": Device.registered_at,
        "last_seen_at": Device.last_seen_at,
    }
    stmt = apply_sort(stmt, sort_map, sort_key, "registered_at", direction)

    page = paginate(stmt)

    return render_template(
        "devices/index.html",
        page=page,
        q=q,
        status_filter=status_filter,
        sort_key=sort_key,
        direction=direction,
    )


@devices_bp.route("/<string:device_id>")
@login_required
def detail(device_id: str):
    device = db.session.get(Device, device_id)
    if device is None:
        abort(404)
    return render_template("devices/detail.html", device=device)


@devices_bp.route("/<string:device_id>/revoke", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def revoke(device_id: str):
    device = db.session.get(Device, device_id)
    if device is None:
        abort(404)

    device.is_active = False
    device.token_revoked_at = datetime.now(timezone.utc)
    device.is_online = False

    log_event(
        EventType.DEVICE_REVOKED,
        f"Device {device.device_name or device.id} revoked by {current_user.username}",
        actor_type=ActorType.ADMIN_USER,
        actor_id=str(current_user.id),
        actor_label=current_user.username,
        target_type="device",
        target_id=device.id,
    )
    db.session.commit()

    return redirect(url_for("devices.detail", device_id=device.id))
