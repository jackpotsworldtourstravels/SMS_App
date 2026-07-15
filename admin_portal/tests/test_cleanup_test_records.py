from app.extensions import db
from app.models.device import Device
from app.models.message import Message


def _seed_dummy_and_real_records(app):
    with app.app_context():
        dummy_device_1 = Device(
            id="3b367883-29c3-4465-9130-c12eab007f84",
            device_name="Reference ID verify",
            api_token_hash="x",
        )
        dummy_device_2 = Device(
            id="99999999-9999-9999-9999-999999999999",
            device_name="Render Deploy Test",
            api_token_hash="x",
        )
        real_device = Device(
            id="10f52fd6-17d6-47bf-9b0a-849a3f32e897",
            device_name="vivo I2217",
            api_token_hash="x",
        )
        db.session.add_all([dummy_device_1, dummy_device_2, real_device])
        db.session.flush()

        dummy_message_1 = Message(
            device_id=dummy_device_1.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.100 debited. Ref No 966697814398",
            category="DEBIT",
            reference_id="966697814398",
            received_at=db.func.now(),
            client_message_id="dummy-1",
        )
        stray_message = Message(
            device_id=real_device.id,
            sender_raw="VM-BOBSMS-S",
            sender_matched="BOBSMS",
            message_body="Test message with no known category.",
            category="UNKNOWN",
            received_at=db.func.now(),
            client_message_id="stray-1",
        )
        real_message = Message(
            device_id=real_device.id,
            sender_raw="AX-HDFCBK-S",
            sender_matched="HDFCBK",
            message_body="Rs.500 credited to your account.",
            category="CREDIT",
            received_at=db.func.now(),
            client_message_id="real-1",
        )
        db.session.add_all([dummy_message_1, stray_message, real_message])
        db.session.commit()


def test_cleanup_test_records_removes_only_dummy_data(app):
    _seed_dummy_and_real_records(app)

    result = app.test_cli_runner().invoke(args=["cleanup-test-records"])
    assert result.exit_code == 0

    with app.app_context():
        assert db.session.get(Device, "3b367883-29c3-4465-9130-c12eab007f84") is None
        assert db.session.get(Device, "99999999-9999-9999-9999-999999999999") is None
        assert db.session.get(Device, "10f52fd6-17d6-47bf-9b0a-849a3f32e897") is not None

        assert Message.query.filter_by(client_message_id="dummy-1").first() is None
        assert Message.query.filter_by(client_message_id="stray-1").first() is None
        assert Message.query.filter_by(client_message_id="real-1").first() is not None


def test_cleanup_test_records_is_idempotent(app):
    _seed_dummy_and_real_records(app)

    runner = app.test_cli_runner()
    first = runner.invoke(args=["cleanup-test-records"])
    second = runner.invoke(args=["cleanup-test-records"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Deleted 0 dummy-device message(s), 0 stray message(s), 0 dummy device(s)." in second.output
