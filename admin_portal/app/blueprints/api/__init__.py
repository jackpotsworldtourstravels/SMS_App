from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from app.blueprints.api.v1 import v1_bp  # noqa: E402

api_bp.register_blueprint(v1_bp, url_prefix="/v1")
