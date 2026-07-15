from datetime import datetime, time

from flask import render_template, request
from flask_login import login_required
from sqlalchemy import cast, select
from sqlalchemy import String as SqlString

from app.blueprints.transactions import transactions_bp
from app.models.device import Device
from app.models.end_user import EndUser
from app.models.message import Message, MessageCategory
from app.utils.query_helpers import apply_search, apply_sort, paginate

# A "transaction" is simply a Message that was successfully classified as
# money moving in or out of the account — this page is a read-only,
# pre-filtered view over the same Message data the Messages page shows,
# not a separate data model.
_TRANSACTION_CATEGORIES = (MessageCategory.CREDIT, MessageCategory.DEBIT)


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


@transactions_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    txn_type = request.args.get("type", "")
    bank = request.args.get("bank", "")
    user_id = request.args.get("user_id", type=int)
    device_id = request.args.get("device_id", "")
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))
    sort_key = request.args.get("sort", "received_at")
    direction = request.args.get("dir", "desc")

    stmt = select(Message).where(Message.category.in_(_TRANSACTION_CATEGORIES))

    if txn_type in _TRANSACTION_CATEGORIES:
        stmt = stmt.where(Message.category == txn_type)
    if bank:
        stmt = stmt.where(Message.sender_matched == bank)
    if user_id:
        stmt = stmt.where(Message.end_user_id == user_id)
    if device_id:
        stmt = stmt.where(Message.device_id == device_id)
    if date_from:
        stmt = stmt.where(Message.received_at >= date_from)
    if date_to:
        stmt = stmt.where(
            Message.received_at <= datetime.combine(date_to.date(), time.max)
        )

    stmt = apply_search(
        stmt,
        [
            Message.message_body,
            Message.sender_raw,
            Message.sender_matched,
            Message.reference_id,
            cast(Message.amount, SqlString),
        ],
        q,
    )

    sort_map = {
        "received_at": Message.received_at,
        "amount": Message.amount,
        "reference_id": Message.reference_id,
        "sender_matched": Message.sender_matched,
    }
    stmt = apply_sort(stmt, sort_map, sort_key, "received_at", direction)

    page = paginate(stmt)

    users = EndUser.query.order_by(EndUser.name).all()
    devices = Device.query.order_by(Device.device_name).all()
    banks = [
        row[0]
        for row in Message.query.with_entities(Message.sender_matched)
        .filter(Message.category.in_(_TRANSACTION_CATEGORIES))
        .distinct()
        .order_by(Message.sender_matched)
        .all()
    ]

    return render_template(
        "transactions/index.html",
        page=page,
        q=q,
        txn_type=txn_type,
        bank=bank,
        user_id=user_id,
        device_id=device_id,
        date_from=request.args.get("date_from", ""),
        date_to=request.args.get("date_to", ""),
        sort_key=sort_key,
        direction=direction,
        users=users,
        devices=devices,
        banks=banks,
    )
