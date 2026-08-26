from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentAction(StrEnum):
    ASK_ONBOARDING_INFO = "ASK_ONBOARDING_INFO"
    ASK_MEETING_DETAILS = "ASK_MEETING_DETAILS"
    PRESENT_PROPOSAL = "PRESENT_PROPOSAL"
    REQUEST_CONFIRMATION = "REQUEST_CONFIRMATION"
    NONE = "NONE"


class AgentOutput(BaseModel):
    intent: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    proposed_reply_draft: str = Field(min_length=1)
    requested_action: AgentAction
