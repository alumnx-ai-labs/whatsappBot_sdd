from app.conversation.idempotency_service import IdempotencyService


def test_duplicate_message_replays_cached_response(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    service = IdempotencyService()
    response = {"handled": False}
    with Session(test_db_engine) as db:
        first = service.claim(
            db,
            message_id="message-1",
            canonical_phone="+919494151816",
            normalized_text="hello",
            raw_payload={"text": "hello"},
        )
        assert first.is_duplicate is False

        service.complete(db, first.message, response)
        second = service.claim(
            db,
            message_id="message-1",
            canonical_phone="+919494151816",
            normalized_text="hello",
            raw_payload={"text": "hello"},
        )

        assert second.is_duplicate is True
        assert second.cached_response == response
