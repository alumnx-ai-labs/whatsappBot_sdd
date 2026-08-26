from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import InboundMessage


@dataclass(frozen=True)
class IdempotencyClaim:
    message: InboundMessage
    is_duplicate: bool
    cached_response: dict | None


class IdempotencyService:
    def claim(
        self,
        db: Session,
        *,
        message_id: str,
        canonical_phone: str,
        normalized_text: str,
        raw_payload: dict,
    ) -> IdempotencyClaim:
        existing = db.scalar(select(InboundMessage).where(InboundMessage.message_id == message_id))
        if existing is not None:
            return IdempotencyClaim(
                message=existing,
                is_duplicate=True,
                cached_response=existing.cached_response,
            )

        message = InboundMessage(
            message_id=message_id,
            canonical_phone=canonical_phone,
            normalized_text=normalized_text,
            raw_payload=raw_payload,
            processing_status="RECEIVED",
        )
        db.add(message)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(
                select(InboundMessage).where(InboundMessage.message_id == message_id)
            )
            if existing is None:
                raise
            return IdempotencyClaim(
                message=existing,
                is_duplicate=True,
                cached_response=existing.cached_response,
            )
        db.refresh(message)
        return IdempotencyClaim(message=message, is_duplicate=False, cached_response=None)

    def complete(
        self,
        db: Session,
        message: InboundMessage,
        response: dict,
        session_id: str | None = None,
    ) -> None:
        message.cached_response = response
        message.processing_status = "PROCESSED"
        message.session_id = session_id
        db.commit()
