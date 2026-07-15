from datetime import datetime, timezone

from flask import current_app, g, jsonify, request
from pydantic import ValidationError

from app.blueprints.api.v1 import v1_bp
from app.blueprints.api.v1.auth import require_device_token
from app.blueprints.api.v1.schemas import HeartbeatRequest, RegisterDeviceRequest
from app.extensions import db
from app.models.audit_log import ActorType, EventType
from app.models.device import Device
from app.services.audit import log_event
from app.services.bank_sender_ids import BANK_SENDER_IDS
from app.services.tokens import generate_api_token, hash_token


@v1_bp.route("/register-device", methods=["POST"])
def register_device():
    try:
        payload = RegisterDeviceRequest.model_validate(request.get_json(force=True, silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "details": exc.errors()}), 400

    device = db.session.get(Device, payload.device_id)
    raw_token = generate_api_token()
    now = datetime.now(timezone.utc)

    if device is not None:
        if not device.is_active:
            return jsonify({"error": "device_revoked"}), 403

        device.api_token_hash = hash_token(raw_token)
        device.token_created_at = now
        device.token_revoked_at = None
        rotated = True
    else:
        device = Device(
            id=payload.device_id,
            api_token_hash=hash_token(raw_token),
            token_created_at=now,
        )
        db.session.add(device)
        rotated = False

    device.device_name = payload.device_name
    device.manufacturer = payload.manufacturer
    device.model = payload.model
    device.android_version = payload.android_version
    device.app_version_name = payload.app_version_name
    device.app_version_code = payload.app_version_code
    device.last_seen_at = now
    device.is_online = True

    log_event(
        EventType.DEVICE_REGISTER,
        f"Device {device.device_name or device.id} "
        f"{'re-registered (token rotated)' if rotated else 'registered'}",
        actor_type=ActorType.DEVICE,
        actor_id=device.id,
        actor_label=device.device_name,
        target_type="device",
        target_id=device.id,
        meta={"rotated": rotated},
    )
    db.session.commit()

    return jsonify(
        {
            "device_id": device.id,
            "api_token": raw_token,
            "heartbeat_interval_seconds": current_app.config["HEARTBEAT_INTERVAL_SECONDS"],
            "server_time": now.isoformat(),
        }
    ), 201 if not rotated else 200


@v1_bp.route("/heartbeat", methods=["POST"])
@require_device_token
def heartbeat():
    try:
        HeartbeatRequest.model_validate(request.get_json(force=True, silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "details": exc.errors()}), 400

    device: Device = g.current_device
    now = datetime.now(timezone.utc)
    device.last_seen_at = now
    device.is_online = True
    db.session.commit()

    return jsonify(
        {
            "status": "ok",
            "server_time": now.isoformat(),
            "heartbeat_interval_seconds": current_app.config["HEARTBEAT_INTERVAL_SECONDS"],
        }
    )


@v1_bp.route("/device-config", methods=["GET"])
@require_device_token
def device_config():
    return jsonify(
        {
            "heartbeat_interval_seconds": current_app.config["HEARTBEAT_INTERVAL_SECONDS"],
            "bank_sender_ids": sorted(BANK_SENDER_IDS),
            "min_app_version_code": 1,
        }
    )
