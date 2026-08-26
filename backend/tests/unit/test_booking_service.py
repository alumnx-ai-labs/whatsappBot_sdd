import pytest
from sqlalchemy.orm import Session

from app.booking.booking_service import BookingService
from app.db.models import ConversationSession, Customer
from app.integrations.hello_oscar.hello_oscar_client import StubHelloOscarClient


@pytest.mark.asyncio
async def test_provider_success_is_the_only_confirmed_outcome(test_db_engine) -> None:
    with Session(test_db_engine) as db:
        customer = Customer(canonical_phone="+919494151816", name="Jane Doe", business_name="Acme")
        session = ConversationSession(canonical_phone=customer.canonical_phone)
        db.add_all([customer, session])
        db.commit()
        db.refresh(customer)
        db.refresh(session)

        booking = await BookingService(
            StubHelloOscarClient(result={"status": "confirmed", "external_booking_id": "HO-1"})
        ).create_and_resolve(
            db,
            session=session,
            customer=customer,
            context={
                "meeting_date": "2026-09-01",
                "meeting_time": "2pm",
                "location": "Office",
            },
            correlation_id="correlation-1",
        )

        assert booking.status == "CONFIRMED"
        assert booking.external_booking_id == "HO-1"


@pytest.mark.asyncio
async def test_provider_failure_is_not_confirmed(test_db_engine) -> None:
    with Session(test_db_engine) as db:
        customer = Customer(canonical_phone="+919494151816", name="Jane Doe", business_name="Acme")
        session = ConversationSession(canonical_phone=customer.canonical_phone)
        db.add_all([customer, session])
        db.commit()
        db.refresh(customer)
        db.refresh(session)

        booking = await BookingService(
            StubHelloOscarClient(result={"status": "failed", "reason": "rejected"})
        ).create_and_resolve(
            db,
            session=session,
            customer=customer,
            context={
                "meeting_date": "2026-09-01",
                "meeting_time": "2pm",
                "location": "Office",
            },
            correlation_id="correlation-1",
        )

        assert booking.status == "FAILED"
        assert booking.external_booking_id is None
