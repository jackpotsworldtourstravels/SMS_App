from datetime import datetime, timezone

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.extensions import db
from app.models.admin_user import AdminUser
from app.models.audit_log import ActorType, EventType
from app.services.audit import log_event


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data.strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password.", "error")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("This account has been disabled.", "error")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=False)
        user.last_login_at = datetime.now(timezone.utc)
        log_event(
            EventType.LOGIN,
            f"{user.username} logged in",
            actor_type=ActorType.ADMIN_USER,
            actor_id=str(user.id),
            actor_label=user.username,
        )
        db.session.commit()

        next_url = request.args.get("next")
        return redirect(next_url or url_for("dashboard.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    log_event(
        EventType.LOGOUT,
        f"{current_user.username} logged out",
        actor_type=ActorType.ADMIN_USER,
        actor_id=str(current_user.id),
        actor_label=current_user.username,
    )
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))
