from flask import Blueprint

v1_bp = Blueprint("api_v1", __name__)

from app.blueprints.api.v1 import devices, messages, dashboard  # noqa: E402,F401
