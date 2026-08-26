from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ConversationSession


def find_active_session(db: Session, canonical_phone: str) -> ConversationSession | None:
    return db.scalar(
        select(ConversationSession)
        .where(
            ConversationSession.canonical_phone == canonical_phone,
            ConversationSession.is_active.is_(True),
        )
        .order_by(ConversationSession.updated_at.desc())
    )


def create_session(
    db: Session, canonical_phone: str, customer_id: str | None = None
) -> ConversationSession:
    session = ConversationSession(
        canonical_phone=canonical_phone,
        customer_id=customer_id,
        state="ONBOARDING",
        is_active=True,
        context={},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
