from flask_login import login_required

from app.blueprints.dashboard import dashboard_bp
from app.services.dashboard_stats import get_dashboard_stats


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    from flask import render_template

    stats = get_dashboard_stats()
    return render_template("dashboard/index.html", stats=stats)
