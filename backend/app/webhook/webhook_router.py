from typing import Any

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.agent.langchain_agent import LangChainAgent
from app.booking.booking_service import BookingService
from app.business_rules.confirmation_rules import is_explicit_confirmation
from app.conversation.conversation_session_service import ConversationSessionService
from app.conversation.idempotency_service import IdempotencyService
from app.db.customer_repository import create_customer
from app.db.models import ConversationSession, Customer
from app.db.session import get_db
from app.shared.errors import AppError
from app.shared.logging import get_logger
from app.webhook.ownership_detector import is_owned_message
from app.webhook.payload_normalizer import PayloadNormalizationError, normalize_payload
from app.webhook.phone_normalizer import InvalidPhoneNumberError, normalize_phone

router = APIRouter(tags=["webhook"])
_session_service = ConversationSessionService()
_idempotency_service = IdempotencyService()
_agent = LangChainAgent()
_booking_service = BookingService()


def _proposal_reply(context: dict[str, Any]) -> str:
    return (
        "Here are the meeting details:\n"
        f"Date: {context['meeting_date']}\n"
        f"Time: {context['meeting_time']}\n"
        f"Location: {context['location']}\n\n"
        "Please reply yes to confirm, or tell me what you would like to change."
    )


def _outcome_reply(status: str) -> str:
    if status == "CONFIRMED":
        return "Your meeting is confirmed. I will see you then."
    if status == "FAILED":
        return (
            "The meeting could not be confirmed. Please share another time or "
            "location to try again."
        )
    return (
        "I could not verify the meeting outcome yet. Please try again later while we reconcile it."
    )


def _merge_customer_context(
    session: ConversationSession, customer: Customer | None
) -> dict[str, Any]:
    context = dict(session.context or {})
    if customer is not None:
        context.setdefault("name", customer.name)
        context.setdefault("business_name", customer.business_name)
    return context


@router.post("/webhook-sync")
async def webhook_sync(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    x_provider_delivery_id: str | None = Header(default=None),
) -> dict[str, Any]:
    request_logger = get_logger("webhook")
    try:
        normalized = normalize_payload(payload, provider_delivery_id=x_provider_delivery_id)
        canonical_phone = normalize_phone(normalized.phone)
    except (PayloadNormalizationError, InvalidPhoneNumberError) as exc:
        raise AppError(400, "invalid_payload", str(exc)) from exc

    claim = _idempotency_service.claim(
        db,
        message_id=normalized.message_id,
        canonical_phone=canonical_phone,
        normalized_text=normalized.text,
        raw_payload=payload,
    )
    correlation_id = normalized.message_id
    request_logger = get_logger("webhook", correlation_id)
    request_logger.info("inbound_message_received")
    if claim.is_duplicate and claim.cached_response is not None:
        return claim.cached_response

    active_session = _session_service.find_active(db, canonical_phone)
    if not is_owned_message(
        text=normalized.text,
        has_active_session=active_session is not None,
    ):
        request_logger.info("message_not_owned")
        response = {"handled": False}
        _idempotency_service.complete(db, claim.message, response)
        return response

    resolution = _session_service.get_or_create(db, canonical_phone)
    session = resolution.session
    customer = resolution.customer
    context = _merge_customer_context(session, customer)

    if session.state == "CONFIRMATION_PENDING" and is_explicit_confirmation(normalized.text):
        request_logger.info("explicit_confirmation_received")
        if customer is None:
            response = {
                "handled": True,
                "reply": "I need your name and business name before I can book the meeting.",
            }
        else:
            booking = await _booking_service.create_and_resolve(
                db,
                session=session,
                customer=customer,
                context=context,
                correlation_id=f"{session.id}:{normalized.message_id}",
            )
            request_logger.info("booking_resolved", extra={"booking_status": booking.status})
            response = {"handled": True, "reply": _outcome_reply(booking.status)}
    else:
        request_logger.info("agent_invocation")
        agent_result = _agent.invoke(text=normalized.text, context=context)
        context.update(agent_result.extracted_fields)

        if customer is None and context.get("name") and context.get("business_name"):
            customer = create_customer(
                db,
                canonical_phone=canonical_phone,
                name=str(context["name"]),
                business_name=str(context["business_name"]),
            )
            session.customer_id = customer.id

        session.context = context
        if agent_result.missing_fields:
            session.state = (
                "ONBOARDING"
                if any(field in ("name", "business_name") for field in agent_result.missing_fields)
                else "COLLECTING_MEETING_INFO"
            )
            response = {"handled": True, "reply": agent_result.proposed_reply_draft}
        else:
            session.state = "CONFIRMATION_PENDING"
            response = {"handled": True, "reply": _proposal_reply(context)}

        db.commit()
    _idempotency_service.complete(db, claim.message, response, session_id=resolution.session.id)
    request_logger.info("reply_persisted")
    return response
