from flask import Blueprint

download_bp = Blueprint("download", __name__, url_prefix="/download")

from app.blueprints.download import routes  # noqa: E402,F401
