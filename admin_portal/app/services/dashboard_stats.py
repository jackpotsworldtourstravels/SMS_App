from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.extensions import db
from app.models.device import Device
from app.models.end_user import EndUser
from app.models.message import Message, MessageCategory


def _today_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def get_dashboard_stats() -> dict:
    devices_total = db.session.scalar(select(func.count(Device.id))) or 0
    devices_online = (
        db.session.scalar(
            select(func.count(Device.id)).where(
                Device.is_active.is_(True), Device.is_online.is_(True)
            )
        )
        or 0
    )
    devices_offline = devices_total - devices_online

    users_total = db.session.scalar(select(func.count(EndUser.id))) or 0

    messages_total = db.session.scalar(select(func.count(Message.id))) or 0

    def _count_category(category: str) -> int:
        return (
            db.session.scalar(
                select(func.count(Message.id)).where(Message.category == category)
            )
            or 0
        )

    messages_otp = _count_category(MessageCategory.OTP)
    messages_credit = _count_category(MessageCategory.CREDIT)
    messages_debit = _count_category(MessageCategory.DEBIT)

    messages_unknown = _count_category(MessageCategory.UNKNOWN)

    messages_today = (
        db.session.scalar(
            select(func.count(Message.id)).where(
                Message.received_at >= _today_start_utc()
            )
        )
        or 0
    )

    transactions_today = (
        db.session.scalar(
            select(func.count(Message.id)).where(
                Message.received_at >= _today_start_utc(),
                Message.category.in_((MessageCategory.CREDIT, MessageCategory.DEBIT)),
            )
        )
        or 0
    )

    return {
        "devices_total": devices_total,
        "devices_online": devices_online,
        "devices_offline": devices_offline,
        "users_total": users_total,
        "messages_total": messages_total,
        "messages_otp": messages_otp,
        "messages_credit": messages_credit,
        "messages_debit": messages_debit,
        "messages_unknown": messages_unknown,
        "messages_today": messages_today,
        "transactions_today": transactions_today,
        "avg_processing_seconds": get_average_processing_seconds(),
    }


def get_average_processing_seconds() -> float | None:
    """Average delay between a message being received on-device and
    landing in the portal, across messages that have both timestamps.
    Purely descriptive — derived from existing received_at/uploaded_at
    columns, no new data collected."""

    rows = db.session.execute(
        select(Message.received_at, Message.uploaded_at).where(
            Message.received_at.is_not(None), Message.uploaded_at.is_not(None)
        )
    ).all()
    if not rows:
        return None

    deltas = [
        (uploaded_at - received_at).total_seconds()
        for received_at, uploaded_at in rows
    ]
    positive_deltas = [d for d in deltas if d >= 0]
    if not positive_deltas:
        return None
    return sum(positive_deltas) / len(positive_deltas)


def get_transactions_per_day(days: int = 14) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day_expr = func.date(Message.received_at)
    rows = db.session.execute(
        select(
            day_expr.label("day"),
            Message.category,
            func.count(Message.id).label("count"),
        )
        .where(
            Message.received_at >= since,
            Message.category.in_((MessageCategory.CREDIT, MessageCategory.DEBIT)),
        )
        .group_by(day_expr, Message.category)
        .order_by(day_expr)
    ).all()
    return [
        {"date": str(row.day), "category": row.category, "count": row.count}
        for row in rows
    ]


def get_top_banks(limit: int = 6) -> list[dict]:
    rows = db.session.execute(
        select(Message.sender_matched, func.count(Message.id).label("count"))
        .where(Message.category.in_((MessageCategory.CREDIT, MessageCategory.DEBIT)))
        .group_by(Message.sender_matched)
        .order_by(func.count(Message.id).desc())
        .limit(limit)
    ).all()
    return [{"bank": bank, "count": count} for bank, count in rows]


def get_top_users(limit: int = 6) -> list[dict]:
    rows = db.session.execute(
        select(EndUser.name, func.count(Message.id).label("count"))
        .join(Message, Message.end_user_id == EndUser.id)
        .group_by(EndUser.id, EndUser.name)
        .order_by(func.count(Message.id).desc())
        .limit(limit)
    ).all()
    return [{"user": name, "count": count} for name, count in rows]


def get_hourly_activity() -> list[dict]:
    hour_expr = func.extract("hour", Message.received_at)
    rows = db.session.execute(
        select(hour_expr.label("hour"), func.count(Message.id).label("count"))
        .group_by(hour_expr)
        .order_by(hour_expr)
    ).all()
    counts_by_hour = {int(row.hour): row.count for row in rows}
    return [{"hour": h, "count": counts_by_hour.get(h, 0)} for h in range(24)]


def get_messages_per_day(days: int = 14) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day_expr = func.date(Message.received_at)
    rows = db.session.execute(
        select(day_expr.label("day"), func.count(Message.id).label("count"))
        .where(Message.received_at >= since)
        .group_by(day_expr)
        .order_by(day_expr)
    ).all()
    return [{"date": str(row.day), "count": row.count} for row in rows]


def get_category_distribution() -> list[dict]:
    rows = db.session.execute(
        select(Message.category, func.count(Message.id))
        .group_by(Message.category)
    ).all()
    return [{"category": category, "count": count} for category, count in rows]


def get_device_status_split() -> list[dict]:
    stats = get_dashboard_stats()
    return [
        {"status": "online", "count": stats["devices_online"]},
        {"status": "offline", "count": stats["devices_offline"]},
    ]


def get_recent_activity(limit: int = 10) -> list[dict]:
    activity: list[dict] = []

    recent_devices = db.session.execute(
        select(Device).order_by(Device.registered_at.desc()).limit(limit)
    ).scalars().all()
    for device in recent_devices:
        activity.append(
            {
                "type": "device_connected",
                "label": f"{device.device_name or device.id} registered",
                "at": device.registered_at,
            }
        )

    recent_messages = db.session.execute(
        select(Message).order_by(Message.uploaded_at.desc()).limit(limit)
    ).scalars().all()
    for message in recent_messages:
        activity.append(
            {
                "type": "message_uploaded",
                "label": f"{message.category} message from {message.sender_matched}",
                "at": message.uploaded_at,
            }
        )

    recent_users = db.session.execute(
        select(EndUser).order_by(EndUser.created_at.desc()).limit(limit)
    ).scalars().all()
    for user in recent_users:
        activity.append(
            {
                "type": "user_registered",
                "label": f"{user.name} added",
                "at": user.created_at,
            }
        )

    activity.sort(key=lambda item: item["at"], reverse=True)
    return activity[:limit]
