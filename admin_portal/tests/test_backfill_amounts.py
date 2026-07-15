import uuid
from decimal import Decimal

from app.extensions import db
from app.models.device import Device
from app.models.message import Message


def _seed(app):
    with app.app_context():
        device = Device(id=str(uuid.uuid4()), device_name="Test Phone", api_token_hash="x")
        db.session.add(device)
        db.session.flush()

        missing_amount = Message(
            device_id=device.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.500.00 debited from A/c XX1234.",
            category="DEBIT",
            amount=None,
            received_at=db.func.now(),
            client_message_id="missing-amount",
        )
        already_has_amount = Message(
            device_id=device.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.999 debited from A/c XX1234.",
            category="DEBIT",
            amount=Decimal("1.00"),
            received_at=db.func.now(),
            client_message_id="has-amount",
        )
        genuinely_no_amount = Message(
            device_id=device.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="123456 is your OTP. Do not share it.",
            category="OTP",
            amount=None,
            received_at=db.func.now(),
            client_message_id="no-amount",
        )
        db.session.add_all([missing_amount, already_has_amount, genuinely_no_amount])
        db.session.commit()


def test_backfill_amounts_updates_only_null_amounts(app):
    _seed(app)

    result = app.test_cli_runner().invoke(args=["backfill-amounts"])
    assert result.exit_code == 0

    with app.app_context():
        updated = Message.query.filter_by(client_message_id="missing-amount").first()
        assert updated.amount == Decimal("500.00")

        untouched = Message.query.filter_by(client_message_id="has-amount").first()
        assert untouched.amount == Decimal("1.00")

        still_none = Message.query.filter_by(client_message_id="no-amount").first()
        assert still_none.amount is None


def test_backfill_amounts_is_idempotent(app):
    _seed(app)

    runner = app.test_cli_runner()
    first = runner.invoke(args=["backfill-amounts"])
    second = runner.invoke(args=["backfill-amounts"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "updated 0 with an amount" in second.output
