from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.business_rules.expiry_service import expire_if_stale
from app.conversation.conversation_session_repository import create_session, find_active_session
from app.db.customer_repository import find_customer_by_phone
from app.db.models import ConversationSession, Customer
from app.shared.config import settings


@dataclass(frozen=True)
class SessionResolution:
    session: ConversationSession
    customer: Customer | None
    is_new_visitor: bool


class ConversationSessionService:
    def find_active(self, db: Session, canonical_phone: str) -> ConversationSession | None:
        session = find_active_session(db, canonical_phone)
        if session is not None:
            expire_if_stale(
                db,
                session,
                expiry_minutes=settings.proposal_expiry_minutes,
            )
            if not session.is_active:
                return None
        return session

    def get_or_create(self, db: Session, canonical_phone: str) -> SessionResolution:
        session = self.find_active(db, canonical_phone)
        customer = find_customer_by_phone(db, canonical_phone)

        if session is None:
            session = create_session(
                db, canonical_phone, customer_id=customer.id if customer else None
            )

        return SessionResolution(
            session=session,
            customer=customer,
            is_new_visitor=customer is None,
        )
