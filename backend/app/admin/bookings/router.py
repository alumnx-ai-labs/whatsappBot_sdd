from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin.auth.require_session import require_admin_session
from app.db.models import AdminUser, Booking
from app.db.session import get_db

router = APIRouter(prefix="/admin/bookings", tags=["admin-bookings"])


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    customer_name: str = Field(alias="customerName")
    business_name: str = Field(alias="businessName")
    meeting_date: date = Field(alias="meetingDate")
    meeting_time: str = Field(alias="meetingTime")
    location: str
    status: str
    external_booking_id: str | None = Field(alias="externalBookingId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


@router.get("", response_model=dict)
def list_confirmed_bookings(
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> dict:
    bookings = db.scalars(
        select(Booking).where(Booking.status == "CONFIRMED").order_by(Booking.created_at.desc())
    ).all()
    return {
        "bookings": [
            BookingResponse.model_validate(item).model_dump(by_alias=True) for item in bookings
        ],
        "total": len(bookings),
    }


@router.get("/{booking_id}", response_model=BookingResponse)
def get_confirmed_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin_session),
) -> Booking:
    booking = db.scalar(
        select(Booking).where(Booking.id == booking_id, Booking.status == "CONFIRMED")
    )
    if booking is None:
        from app.shared.errors import AppError

        raise AppError(404, "not_found", "Confirmed booking not found")
    return booking
