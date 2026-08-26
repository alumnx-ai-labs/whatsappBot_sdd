from app.conversation.idempotency_service import IdempotencyService
from app.db.models import InboundMessage


def test_existing_message_is_replayed_after_claim_attempt(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    service = IdempotencyService()
    with Session(test_db_engine) as db:
        message = InboundMessage(
            message_id="race-1",
            canonical_phone="+919494151816",
            normalized_text="hello",
            raw_payload={"text": "hello"},
            cached_response={"handled": False},
            processing_status="PROCESSED",
        )
        db.add(message)
        db.commit()

        result = service.claim(
            db,
            message_id="race-1",
            canonical_phone="+919494151816",
            normalized_text="hello",
            raw_payload={"text": "hello"},
        )

        assert result.is_duplicate is True
        assert result.cached_response == {"handled": False}
        assert db.query(InboundMessage).filter_by(message_id="race-1").count() == 1
