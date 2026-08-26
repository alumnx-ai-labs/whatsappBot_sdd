from datetime import UTC, datetime, timedelta

from app.business_rules.expiry_service import expire_if_stale
from app.db.models import ConversationSession


def test_proposal_is_active_at_t_minus_one(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    with Session(test_db_engine) as db:
        session = ConversationSession(canonical_phone="+919494151816", state="PROPOSED")
        db.add(session)
        db.commit()
        session.updated_at = now - timedelta(minutes=29, seconds=59)
        db.commit()

        assert expire_if_stale(db, session, expiry_minutes=30, now=now) is False
        assert session.is_active is True


def test_proposal_expires_at_exact_boundary(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    with Session(test_db_engine) as db:
        session = ConversationSession(canonical_phone="+919494151816", state="PROPOSED")
        db.add(session)
        db.commit()
        session.updated_at = now - timedelta(minutes=30)
        db.commit()

        assert expire_if_stale(db, session, expiry_minutes=30, now=now) is True
        assert session.state == "EXPIRED"
        assert session.is_active is False


def test_expired_proposal_stays_expired_at_t_plus_one(test_db_engine) -> None:
    from sqlalchemy.orm import Session

    now = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
    with Session(test_db_engine) as db:
        session = ConversationSession(
            canonical_phone="+919494151816", state="EXPIRED", is_active=False
        )
        db.add(session)
        db.commit()
        session.updated_at = now - timedelta(minutes=31)
        db.commit()

        assert expire_if_stale(db, session, expiry_minutes=30, now=now) is False
        assert session.state == "EXPIRED"
        assert session.is_active is False
