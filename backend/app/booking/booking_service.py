from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.business_rules.booking_state_machine import BookingState
from app.business_rules.meeting_validation import validate_meeting_context
from app.db.models import Booking, BookingStateTransition, ConversationSession, Customer
from app.integrations.hello_oscar.hello_oscar_client import (
    HelloOscarClient,
    HelloOscarRequest,
    UnresolvedResult,
)


class BookingService:
    def __init__(self, provider: HelloOscarClient | None = None) -> None:
        self.provider = provider or HelloOscarClient()

    async def create_and_resolve(
        self,
        db: Session,
        *,
        session: ConversationSession,
        customer: Customer,
        context: dict,
        correlation_id: str,
    ) -> Booking:
        validate_meeting_context(context)

        existing = db.scalar(
            select(Booking)
            .where(
                Booking.session_id == session.id,
                Booking.status.in_(["BOOKING_IN_PROGRESS", "CONFIRMED", "UNRESOLVED"]),
            )
            .order_by(Booking.created_at.desc())
        )
        if existing is not None:
            return existing

        attempt_id = str(uuid4())
        meeting_date = date.fromisoformat(str(context["meeting_date"]))
        booking = Booking(
            booking_attempt_id=attempt_id,
            customer_id=customer.id,
            customer_name=customer.name,
            business_name=customer.business_name,
            meeting_date=meeting_date,
            meeting_time=str(context["meeting_time"]),
            location=str(context["location"]),
            status=BookingState.BOOKING_IN_PROGRESS.value,
            session_id=session.id,
        )
        db.add(booking)
        db.flush()
        self._transition(db, booking, None, BookingState.BOOKING_IN_PROGRESS, correlation_id)
        session.active_booking_id = booking.id
        db.commit()

        try:
            result = await self.provider.create_booking(
                HelloOscarRequest(
                    booking_attempt_id=attempt_id,
                    customer_name=customer.name,
                    business_name=customer.business_name,
                    meeting_date=meeting_date.isoformat(),
                    meeting_time=str(context["meeting_time"]),
                    location=str(context["location"]),
                )
            )
        except TimeoutError:
            result = UnresolvedResult(status="unresolved", reason="provider timeout")
        except Exception:
            result = UnresolvedResult(status="unresolved", reason="provider error")
        if result.status == "confirmed":
            booking.status = BookingState.CONFIRMED.value
            booking.external_booking_id = result.external_booking_id
            session.state = BookingState.CONFIRMED.value
            session.is_active = False
            self._transition(
                db,
                booking,
                BookingState.BOOKING_IN_PROGRESS,
                BookingState.CONFIRMED,
                correlation_id,
            )
        elif result.status == "failed":
            booking.status = BookingState.FAILED.value
            session.state = BookingState.FAILED.value
            self._transition(
                db,
                booking,
                BookingState.BOOKING_IN_PROGRESS,
                BookingState.FAILED,
                correlation_id,
                result.reason,
            )
        else:
            booking.status = BookingState.UNRESOLVED.value
            session.state = BookingState.UNRESOLVED.value
            self._transition(
                db,
                booking,
                BookingState.BOOKING_IN_PROGRESS,
                BookingState.UNRESOLVED,
                correlation_id,
                result.reason,
            )

        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def _transition(
        db: Session,
        booking: Booking,
        from_state: BookingState | None,
        to_state: BookingState,
        correlation_id: str,
        reason: str | None = None,
    ) -> None:
        db.add(
            BookingStateTransition(
                booking_id=booking.id,
                from_status=from_state.value if from_state else None,
                to_status=to_state.value,
                reason=reason,
                correlation_id=correlation_id,
            )
        )
