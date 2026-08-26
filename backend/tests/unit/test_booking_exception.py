import pytest
from sqlalchemy.orm import Session

from app.booking.booking_service import BookingService
from app.db.models import Booking, ConversationSession, Customer
from app.integrations.hello_oscar.hello_oscar_client import HelloOscarClient


class RaisingProvider(HelloOscarClient):
    async def create_booking(self, request):
        raise TimeoutError("provider timed out")


@pytest.mark.asyncio
async def test_provider_exception_becomes_unresolved(test_db_engine) -> None:
    with Session(test_db_engine) as db:
        customer = Customer(canonical_phone="+919494151816", name="Jane", business_name="Acme")
        session = ConversationSession(canonical_phone=customer.canonical_phone)
        db.add_all([customer, session])
        db.commit()
        db.refresh(customer)
        db.refresh(session)

        booking = await BookingService(RaisingProvider()).create_and_resolve(
            db,
            session=session,
            customer=customer,
            context={
                "meeting_date": "2099-09-01",
                "meeting_time": "2pm",
                "location": "Office",
            },
            correlation_id="correlation-1",
        )

        assert booking.status == "UNRESOLVED"
        assert db.query(Booking).count() == 1
