from sqlalchemy.orm import Session

from app.booking.booking_service import BookingService
from app.db.models import Booking, ConversationSession
from app.integrations.hello_oscar.hello_oscar_client import StubHelloOscarClient


def _start_session(test_db_engine, phone: str) -> None:
    with Session(test_db_engine) as db:
        db.add(ConversationSession(canonical_phone=phone, state="ONBOARDING"))
        db.commit()


def test_new_visitor_reaches_confirmed_booking(client, test_db_engine, monkeypatch) -> None:
    import app.webhook.webhook_router as webhook_module

    phone = "+919494151816"
    _start_session(test_db_engine, phone)
    monkeypatch.setattr(
        webhook_module,
        "_booking_service",
        BookingService(
            StubHelloOscarClient(result={"status": "confirmed", "external_booking_id": "HO-123"})
        ),
    )

    name = client.post(
        "/webhook-sync",
        json={"phone": phone, "text": "My name is Jane", "message_id": "flow-name"},
    )
    assert name.json()["handled"] is True

    business = client.post(
        "/webhook-sync",
        json={"phone": phone, "text": "My business is Acme", "message_id": "flow-business"},
    )
    assert business.json()["handled"] is True

    details = client.post(
        "/webhook-sync",
        json={
            "phone": phone,
            "text": "I need a meeting on 2099-09-01 at 2pm at Downtown Office",
            "message_id": "flow-details",
        },
    )
    assert "Please reply yes" in details.json()["reply"]

    confirmation = client.post(
        "/webhook-sync",
        json={"phone": phone, "text": "yes, confirm", "message_id": "flow-confirm"},
    )
    assert "confirmed" in confirmation.json()["reply"].lower()

    with Session(test_db_engine) as db:
        booking = db.query(Booking).one()
        assert booking.status == "CONFIRMED"
        assert booking.external_booking_id == "HO-123"


def test_provider_failure_never_confirms(client, test_db_engine, monkeypatch) -> None:
    import app.webhook.webhook_router as webhook_module

    phone = "+919494151817"
    _start_session(test_db_engine, phone)
    monkeypatch.setattr(
        webhook_module,
        "_booking_service",
        BookingService(StubHelloOscarClient(result={"status": "failed", "reason": "rejected"})),
    )

    for message_id, text in [
        ("failure-name", "My name is John"),
        ("failure-business", "My business is Beta"),
        ("failure-details", "meeting on 2099-09-01 at 4pm at Main Office"),
    ]:
        client.post(
            "/webhook-sync",
            json={"phone": phone, "text": text, "message_id": message_id},
        )

    response = client.post(
        "/webhook-sync",
        json={"phone": phone, "text": "yes", "message_id": "failure-confirm"},
    )
    assert "not be confirmed" in response.json()["reply"]

    with Session(test_db_engine) as db:
        assert db.query(Booking).one().status == "FAILED"
