import logging
from datetime import datetime, timedelta, timezone

from flask import Flask
from sqlalchemy import select

from app.extensions import db
from app.models.audit_log import ActorType, EventType
from app.models.device import Device
from app.services.audit import log_event

logger = logging.getLogger(__name__)


def sweep_offline_devices(app: Flask) -> int:
    """Flip any device whose last_seen_at is past the configured threshold
    to offline, logging a DEVICE_DISCONNECT audit entry for each
    online->offline *transition* (not on every sweep tick). Returns the
    number of devices flipped. Must run inside an app context."""

    threshold_minutes = app.config["DEVICE_OFFLINE_THRESHOLD_MINUTES"]
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)

    stale_devices = db.session.execute(
        select(Device).where(
            Device.is_online.is_(True),
            (Device.last_seen_at.is_(None)) | (Device.last_seen_at < cutoff),
        )
    ).scalars().all()

    for device in stale_devices:
        device.is_online = False
        log_event(
            EventType.DEVICE_DISCONNECT,
            f"Device {device.device_name or device.id} went offline "
            f"(no heartbeat for over {threshold_minutes} minutes)",
            actor_type=ActorType.SYSTEM,
            actor_id=device.id,
            actor_label=device.device_name,
            target_type="device",
            target_id=device.id,
        )

    if stale_devices:
        db.session.commit()
        logger.info("device_status_sweep flipped %d device(s) offline", len(stale_devices))

    return len(stale_devices)
