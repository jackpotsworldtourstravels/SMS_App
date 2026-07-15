from datetime import datetime, timezone

from flask import g, jsonify, request
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.blueprints.api.v1 import v1_bp
from app.blueprints.api.v1.auth import require_device_token
from app.blueprints.api.v1.schemas import MessagesRequest
from app.extensions import db
from app.models.audit_log import ActorType, EventType
from app.models.device import Device
from app.models.message import Message
from app.services.amount_extraction import extract_amount
from app.services.audit import log_event
from app.services.categorization import categorize_message
from app.services.reference_extraction import extract_reference_id


@v1_bp.route("/messages", methods=["POST"])
@require_device_token
def upload_messages():
    try:
        payload = MessagesRequest.model_validate(request.get_json(force=True, silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "details": exc.errors()}), 400

    device: Device = g.current_device
    now = datetime.now(timezone.utc)

    results = []
    accepted = 0
    duplicates = 0
    rejected = 0

    for item in payload.messages:
        existing = Message.query.filter_by(
            device_id=device.id, client_message_id=item.client_message_id
        ).first()

        if existing is not None:
            duplicates += 1
            results.append(
                {
                    "client_message_id": item.client_message_id,
                    "status": "duplicate",
                    "category": existing.category,
                    "message_id": existing.id,
                }
            )
            continue

        category = categorize_message(item.body)
        reference_id = extract_reference_id(item.body)
        amount = extract_amount(item.body)

        message = Message(
            device_id=device.id,
            end_user_id=device.end_user_id,
            sender_raw=item.sender_raw,
            sender_matched=item.sender_matched,
            message_body=item.body,
            category=category,
            reference_id=reference_id,
            amount=amount,
            received_at=item.received_at,
            uploaded_at=now,
            client_message_id=item.client_message_id,
        )
        db.session.add(message)

        try:
            db.session.flush()
        except IntegrityError:
            # Lost a race with a concurrent retry of the same message;
            # treat it as a duplicate rather than failing the whole batch.
            db.session.rollback()
            existing = Message.query.filter_by(
                device_id=device.id, client_message_id=item.client_message_id
            ).first()
            duplicates += 1
            results.append(
                {
                    "client_message_id": item.client_message_id,
                    "status": "duplicate",
                    "category": existing.category if existing else category,
                    "message_id": existing.id if existing else None,
                }
            )
            continue

        accepted += 1
        results.append(
            {
                "client_message_id": item.client_message_id,
                "status": "accepted",
                "category": category,
                "reference_id": reference_id,
                "amount": float(amount) if amount is not None else None,
                "message_id": message.id,
            }
        )

    device.last_seen_at = now
    device.is_online = True

    if accepted > 0:
        log_event(
            EventType.MESSAGE_UPLOAD,
            f"{accepted} message(s) uploaded from {device.device_name or device.id}",
            actor_type=ActorType.DEVICE,
            actor_id=device.id,
            actor_label=device.device_name,
            target_type="device",
            target_id=device.id,
            meta={"accepted": accepted, "duplicates": duplicates, "rejected": rejected},
        )

    db.session.commit()

    return jsonify(
        {
            "accepted": accepted,
            "duplicates": duplicates,
            "rejected": rejected,
            "results": results,
        }
    )
