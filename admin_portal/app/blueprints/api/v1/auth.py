from functools import wraps

from flask import g, jsonify, request

from app.models.device import Device
from app.services.tokens import hash_token

# IMPORTANT: this module is the *only* auth mechanism for the /api/v1
# blueprint, which is CSRF-exempt (see app/__init__.py). Endpoints guarded
# by @require_device_token must never also accept the admin browser session
# (flask_login's current_user) — mixing the two would make the CSRF
# exemption exploitable via a logged-in admin's browser.


def require_device_token(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing_bearer_token"}), 401

        raw_token = auth_header[len("Bearer "):].strip()
        if not raw_token:
            return jsonify({"error": "missing_bearer_token"}), 401

        token_hash = hash_token(raw_token)
        device = Device.query.filter_by(api_token_hash=token_hash).first()

        if device is None or not device.is_token_valid():
            return jsonify({"error": "invalid_or_revoked_token"}), 401

        g.current_device = device
        return view_func(*args, **kwargs)

    return wrapped
