import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    canonical_phone: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    business_name: Mapped[str] = mapped_column(String, nullable=False)
    contact_info: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_interaction_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    sessions: Mapped[list["ConversationSession"]] = relationship(back_populates="customer")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")


class BusinessMetadata(Base):
    __tablename__ = "business_metadata"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    business_name: Mapped[str] = mapped_column(String, nullable=False)
    contact_person: Mapped[str] = mapped_column(String, nullable=False)
    whatsapp_phone: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String, default="FORM")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    canonical_phone: Mapped[str] = mapped_column(String, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String, default="ONBOARDING")
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    active_booking_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer: Mapped[Customer | None] = relationship(back_populates="sessions")
    inbound_messages: Mapped[list["InboundMessage"]] = relationship(back_populates="session")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="session")


class InboundMessage(Base):
    __tablename__ = "inbound_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    message_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    canonical_phone: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    processing_status: Mapped[str] = mapped_column(String, default="RECEIVED")
    cached_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversation_sessions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    session: Mapped[ConversationSession | None] = relationship(back_populates="inbound_messages")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    booking_attempt_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    business_name: Mapped[str] = mapped_column(String, nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_time: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PROPOSED", index=True)
    external_booking_id: Mapped[str | None] = mapped_column(String, nullable=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("conversation_sessions.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer: Mapped[Customer] = relationship(back_populates="bookings")
    session: Mapped[ConversationSession] = relationship(back_populates="bookings")
    transitions: Mapped[list["BookingStateTransition"]] = relationship(back_populates="booking")


class BookingStateTransition(Base):
    __tablename__ = "booking_state_transitions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String, nullable=True)
    to_status: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    booking: Mapped[Booking] = relationship(back_populates="transitions")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CsvUploadBatch(Base):
    __tablename__ = "csv_upload_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    uploaded_by_admin_id: Mapped[str] = mapped_column(ForeignKey("admin_users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    accepted_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    rows: Mapped[list["CsvUploadRow"]] = relationship(back_populates="batch")


class CsvUploadRow(Base):
    __tablename__ = "csv_upload_rows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    batch_id: Mapped[str] = mapped_column(ForeignKey("csv_upload_batches.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String, nullable=False)
    error_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_row_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    batch: Mapped[CsvUploadBatch] = relationship(back_populates="rows")
