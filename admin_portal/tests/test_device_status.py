import uuid
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.audit_log import AuditLog, EventType
from app.models.device import Device
from app.services.device_status import sweep_offline_devices


def _make_device(app, last_seen_at, is_online=True):
    with app.app_context():
        device = Device(
            id=str(uuid.uuid4()),
            device_name="Stale Phone",
            api_token_hash="x",
            is_online=is_online,
            last_seen_at=last_seen_at,
        )
        db.session.add(device)
        db.session.commit()
        return device.id


def test_sweep_flips_stale_device_offline_and_logs_disconnect(app):
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    device_id = _make_device(app, stale_time, is_online=True)

    with app.app_context():
        app.config["DEVICE_OFFLINE_THRESHOLD_MINUTES"] = 20
        flipped = sweep_offline_devices(app)
        assert flipped == 1

        device = db.session.get(Device, device_id)
        assert device.is_online is False

        entry = AuditLog.query.filter_by(event_type=EventType.DEVICE_DISCONNECT).first()
        assert entry is not None
        assert entry.target_id == device_id


def test_sweep_leaves_recently_seen_device_online(app):
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=2)
    device_id = _make_device(app, recent_time, is_online=True)

    with app.app_context():
        app.config["DEVICE_OFFLINE_THRESHOLD_MINUTES"] = 20
        flipped = sweep_offline_devices(app)
        assert flipped == 0

        device = db.session.get(Device, device_id)
        assert device.is_online is True


def test_sweep_does_not_relog_already_offline_devices(app):
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    _make_device(app, stale_time, is_online=False)

    with app.app_context():
        app.config["DEVICE_OFFLINE_THRESHOLD_MINUTES"] = 20
        flipped = sweep_offline_devices(app)
        assert flipped == 0
        assert AuditLog.query.filter_by(event_type=EventType.DEVICE_DISCONNECT).count() == 0
