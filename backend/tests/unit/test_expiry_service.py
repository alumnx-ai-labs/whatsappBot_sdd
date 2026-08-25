from datetime import UTC, datetime, timedelta

from app.business_rules.expiry_service import expire_if_stale
from app.db.models import ConversationSession


def test_stale_confirmation_session_expires_silently(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    with Session(test_db_engine) as db:
        session = ConversationSession(
            canonical_phone="+919494151816",
            state="CONFIRMATION_PENDING",
            context={"meeting_date": "2026-09-01"},
        )
        db.add(session)
        db.commit()
        session.updated_at = datetime.now(UTC) - timedelta(minutes=31)
        db.commit()

        expired = expire_if_stale(db, session, expiry_minutes=30, now=datetime.now(UTC))

        assert expired is True
        assert session.state == "EXPIRED"
        assert session.is_active is False


def test_fresh_session_is_not_expired(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    with Session(test_db_engine) as db:
        session = ConversationSession(canonical_phone="+919494151816", state="PROPOSED", context={})
        db.add(session)
        db.commit()

        assert expire_if_stale(db, session, expiry_minutes=30, now=datetime.now(UTC)) is False
        assert session.is_active is True
