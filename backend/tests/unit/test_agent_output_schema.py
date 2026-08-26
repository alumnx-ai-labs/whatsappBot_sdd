import pytest
from pydantic import ValidationError

from app.agent.output_schemas import AgentAction, AgentOutput


def test_agent_output_accepts_only_non_transactional_actions() -> None:
    result = AgentOutput(
        intent="meeting_request",
        extracted_fields={"location": "Office"},
        missing_fields=["meeting_date"],
        proposed_reply_draft="What date works for you?",
        requested_action=AgentAction.ASK_MEETING_DETAILS,
    )

    assert result.requested_action == AgentAction.ASK_MEETING_DETAILS


def test_agent_cannot_emit_booking_confirmation_action() -> None:
    with pytest.raises(ValidationError):
        AgentOutput(
            intent="meeting_request",
            extracted_fields={},
            missing_fields=[],
            proposed_reply_draft="Confirmed",
            requested_action="CONFIRM_BOOKING",
        )
