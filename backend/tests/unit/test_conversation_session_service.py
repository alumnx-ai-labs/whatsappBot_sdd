from app.conversation.conversation_session_service import ConversationSessionService
from app.db.models import Customer


def test_resolves_new_visitor_and_reuses_active_session(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    service = ConversationSessionService()
    with Session(test_db_engine) as db:
        first = service.get_or_create(db, "+919494151816")
        assert first.session.canonical_phone == "+919494151816"
        assert first.customer is None
        assert first.is_new_visitor is True

        db.add(
            Customer(
                canonical_phone="+919494151816",
                name="Jane Doe",
                business_name="Acme",
            )
        )
        db.commit()

        second = service.get_or_create(db, "+919494151816")
        assert second.session.id == first.session.id
        assert second.is_new_visitor is False
        assert second.customer is not None
        assert second.customer.name == "Jane Doe"
