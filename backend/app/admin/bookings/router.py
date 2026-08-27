from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin.auth.require_session import require_admin_session
from app.db.models import AdminUser, Booking, Customer
from app.db.session import get_db

router = APIRouter(prefix="/admin/bookings", tags=["admin-bookings"])


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    customer_name: str = Field(alias="customerName")
    customer_phone: str = Field(alias="customerPhone")
    business_name: str = Field(alias="businessName")
    meeting_date: date = Field(alias="meetingDate")
    meeting_time: str = Field(alias="meetingTime")
    location: str
    status: str
    external_booking_id: str | None = Field(alias="externalBookingId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


def _to_response(booking: Booking) -> dict:
    return BookingResponse(
        id=booking.id,
        customerName=booking.customer_name,
        customerPhone=booking.customer.canonical_phone,
        businessName=booking.business_name,
        meetingDate=booking.meeting_date,
        meetingTime=booking.meeting_time,
        location=booking.location,
        status=booking.status,
        externalBookingId=booking.external_booking_id,
        createdAt=booking.created_at,
        updatedAt=booking.updated_at,
    ).model_dump(by_alias=True)


@router.get("", response_model=dict)
def list_confirmed_bookings(
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> dict:
    bookings = db.scalars(
        select(Booking)
        .join(Customer, Booking.customer_id == Customer.id)
        .where(Booking.status == "CONFIRMED")
        .order_by(Booking.created_at.desc())
    ).all()
    return {
        "bookings": [_to_response(item) for item in bookings],
        "total": len(bookings),
    }


@router.get("/{booking_id}", response_model=dict)
def get_confirmed_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> dict:
    booking = db.scalar(
        select(Booking).where(Booking.id == booking_id, Booking.status == "CONFIRMED")
    )
    if booking is None:
        from app.shared.errors import AppError

        raise AppError(404, "not_found", "Confirmed booking not found")
    return _to_response(booking)
