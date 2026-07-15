from flask import render_template
from flask_login import login_required

from app.blueprints.analytics import analytics_bp
from app.services.dashboard_stats import (
    get_hourly_activity,
    get_top_banks,
    get_top_users,
    get_transactions_per_day,
)


@analytics_bp.route("/")
@login_required
def index():
    return render_template(
        "analytics/index.html",
        top_banks=get_top_banks(),
        top_users=get_top_users(),
        hourly_activity=get_hourly_activity(),
        transactions_per_day=get_transactions_per_day(),
    )
