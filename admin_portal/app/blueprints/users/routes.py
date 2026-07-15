from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.blueprints.users import users_bp
from app.blueprints.users.forms import EndUserForm
from app.extensions import db
from app.models.audit_log import ActorType, EventType
from app.models.device import Device
from app.models.end_user import EndUser, EndUserStatus
from app.services.audit import log_event
from app.utils.query_helpers import apply_search, apply_sort, paginate


def _linkable_device_choices(current_device_id: str | None = None):
    stmt = select(Device).where(Device.is_active.is_(True))
    if current_device_id:
        stmt = stmt.where(
            (Device.end_user_id.is_(None)) | (Device.id == current_device_id)
        )
    else:
        stmt = stmt.where(Device.end_user_id.is_(None))

    devices = db.session.execute(stmt.order_by(Device.registered_at.desc())).scalars().all()
    choices = [("", "-- No device --")] + [
        (d.id, f"{d.device_name or d.id} ({d.id[:8]})") for d in devices
    ]
    return choices


@users_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    sort_key = request.args.get("sort", "created_at")
    direction = request.args.get("dir", "desc")

    stmt = select(EndUser)

    if status_filter in (EndUserStatus.ACTIVE, EndUserStatus.DISABLED):
        stmt = stmt.where(EndUser.status == status_filter)

    stmt = apply_search(stmt, [EndUser.name, EndUser.phone_number], q)

    sort_map = {
        "name": EndUser.name,
        "created_at": EndUser.created_at,
    }
    stmt = apply_sort(stmt, sort_map, sort_key, "created_at", direction)

    page = paginate(stmt)

    return render_template(
        "users/index.html",
        page=page,
        q=q,
        status_filter=status_filter,
        sort_key=sort_key,
        direction=direction,
    )


@users_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = EndUserForm()
    form.device_id.choices = _linkable_device_choices()

    if form.validate_on_submit():
        user = EndUser(
            name=form.name.data.strip(),
            phone_number=form.phone_number.data.strip() or None,
            notes=form.notes.data.strip() or None,
            created_by_admin_id=current_user.id,
        )
        db.session.add(user)
        db.session.flush()

        if form.device_id.data:
            device = db.session.get(Device, form.device_id.data)
            if device is not None:
                device.end_user_id = user.id

        log_event(
            EventType.USER_CREATE,
            f"User {user.name} created by {current_user.username}",
            actor_type=ActorType.ADMIN_USER,
            actor_id=str(current_user.id),
            actor_label=current_user.username,
            target_type="end_user",
            target_id=str(user.id),
        )
        db.session.commit()
        flash(f"User {user.name} created.", "success")
        return redirect(url_for("users.index"))

    return render_template("users/form.html", form=form, mode="new")


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit(user_id: int):
    user = db.session.get(EndUser, user_id)
    if user is None:
        abort(404)

    current_device = db.session.execute(
        select(Device).where(Device.end_user_id == user.id)
    ).scalar_one_or_none()

    form = EndUserForm(obj=user)
    form.device_id.choices = _linkable_device_choices(
        current_device.id if current_device else None
    )

    if request.method == "GET" and current_device:
        form.device_id.data = current_device.id

    if form.validate_on_submit():
        user.name = form.name.data.strip()
        user.phone_number = form.phone_number.data.strip() or None
        user.notes = form.notes.data.strip() or None

        if current_device and current_device.id != form.device_id.data:
            current_device.end_user_id = None

        if form.device_id.data:
            new_device = db.session.get(Device, form.device_id.data)
            if new_device is not None:
                new_device.end_user_id = user.id

        log_event(
            EventType.USER_UPDATE,
            f"User {user.name} updated by {current_user.username}",
            actor_type=ActorType.ADMIN_USER,
            actor_id=str(current_user.id),
            actor_label=current_user.username,
            target_type="end_user",
            target_id=str(user.id),
        )
        db.session.commit()
        flash(f"User {user.name} updated.", "success")
        return redirect(url_for("users.index"))

    return render_template("users/form.html", form=form, mode="edit", user=user)


@users_bp.route("/<int:user_id>/disable", methods=["POST"])
@login_required
def disable(user_id: int):
    user = db.session.get(EndUser, user_id)
    if user is None:
        abort(404)

    user.status = EndUserStatus.DISABLED

    log_event(
        EventType.USER_UPDATE,
        f"User {user.name} disabled by {current_user.username}",
        actor_type=ActorType.ADMIN_USER,
        actor_id=str(current_user.id),
        actor_label=current_user.username,
        target_type="end_user",
        target_id=str(user.id),
    )
    db.session.commit()
    flash(f"User {user.name} disabled.", "success")
    return redirect(url_for("users.index"))
