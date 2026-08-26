from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import ConversationSession

_EXPIRABLE_STATES = {"PROPOSED", "CONFIRMATION_PENDING"}


def expire_if_stale(
    db: Session,
    session: ConversationSession,
    *,
    expiry_minutes: int,
    now: datetime | None = None,
) -> bool:
    current_time = now or datetime.now(UTC)
    updated_at = session.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)

    age_seconds = (current_time - updated_at).total_seconds()
    if session.state not in _EXPIRABLE_STATES or age_seconds <= expiry_minutes * 60:
        return False

    session.state = "EXPIRED"
    session.is_active = False
    session.context = {}
    db.commit()
    return True
