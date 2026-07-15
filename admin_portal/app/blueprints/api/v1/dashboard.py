from flask import jsonify
from flask_login import login_required

from app.blueprints.api.v1 import v1_bp
from app.services.dashboard_stats import (
    get_category_distribution,
    get_dashboard_stats,
    get_device_status_split,
    get_messages_per_day,
    get_recent_activity,
)


@v1_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    activity = [
        {
            "type": item["type"],
            "label": item["label"],
            "at": item["at"].isoformat() if item["at"] else None,
        }
        for item in get_recent_activity()
    ]

    return jsonify(
        {
            "totals": get_dashboard_stats(),
            "messages_per_day": get_messages_per_day(),
            "category_distribution": get_category_distribution(),
            "device_status": get_device_status_split(),
            "recent_activity": activity,
        }
    )
