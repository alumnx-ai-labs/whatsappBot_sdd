import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from langchain.agents import create_agent

from app.agent.output_schemas import AgentAction, AgentOutput
from app.agent.tools.meeting_tools import TOOLS
from app.shared.config import settings


def _business_today() -> date:
    try:
        tz = ZoneInfo(settings.business_timezone)
    except (KeyError, ValueError):
        tz = UTC
    return datetime.now(tz).date()


class LangChainAgent:
    """LangChain agent boundary with a deterministic local fallback for development/tests."""

    def __init__(self, model: Any | None = None, tools: list[Any] | None = None) -> None:
        self.tools = tools if tools is not None else TOOLS
        self.agent = model
        if self.agent is None and settings.google_api_key:
            self.agent = create_agent(
                model="google_genai:gemini-3.6-flash",
                tools=self.tools,
                response_format=AgentOutput,
                system_prompt=(
                    "Interpret WhatsApp meeting requests. Return structured data only. "
                    "Never confirm or create bookings; deterministic backend rules do that."
                ),
            )

    def invoke(self, *, text: str, context: dict) -> AgentOutput:
        if self.agent is not None:
            result = self.agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Conversation context: {context}\nVisitor message: {text}",
                        }
                    ]
                }
            )
            structured_response = (
                result.get("structured_response") if isinstance(result, dict) else result
            )
            return AgentOutput.model_validate(structured_response)

        return self._fallback(text=text, context=context)

    def _fallback(self, *, text: str, context: dict) -> AgentOutput:
        fields: dict[str, str] = {}
        name_match = re.search(
            r"(?:my name is|i am|i'm)\s+([A-Za-z][A-Za-z ]*?)(?=\s+(?:and|,|business)\b|$)",
            text,
            re.I,
        )
        business_match = re.search(
            r"(?:business is|from)\s+([A-Za-z][A-Za-z ]*?)(?=\s+(?:and|for|on|at|in)\b|$)",
            text,
            re.I,
        )
        if name_match and "name" not in context:
            fields["name"] = name_match.group(1).strip()
        if business_match and "business_name" not in context:
            fields["business_name"] = business_match.group(1).strip()

        meeting_intent = re.search(
            r"\b(meeting|meet|appointment|schedule|book|booking)\b", text, re.I
        )
        if "meeting_date" in context or "meeting_time" in context or meeting_intent:
            date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
            if date_match:
                fields["meeting_date"] = date_match.group(1)
            elif "tomorrow" in text.casefold():
                fields["meeting_date"] = (_business_today() + timedelta(days=1)).isoformat()
            elif "today" in text.casefold():
                fields["meeting_date"] = _business_today().isoformat()

            if not date_match:
                weekday_match = re.search(
                    r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
                    text,
                    re.I,
                )
                if weekday_match:
                    target_weekday = [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ].index(weekday_match.group(1).casefold())
                    days_ahead = (target_weekday - _business_today().weekday()) % 7 or 7
                    fields["meeting_date"] = (
                        _business_today() + timedelta(days=days_ahead)
                    ).isoformat()

            time_match = re.search(r"(?<![\d-])\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", text, re.I)
            if time_match:
                fields["meeting_time"] = time_match.group(1).replace(" ", "").lower()
            location_matches = re.findall(
                r"\b(?:at|in)\s+(?!\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b)"
                r"([A-Za-z][A-Za-z0-9 &'-]*?)(?=\s+(?:on|for)\b|[,.]|$)",
                text,
                re.I,
            )
            if location_matches:
                fields["location"] = location_matches[-1].strip()

        merged = {**context, **fields}
        if not merged.get("name") or not merged.get("business_name"):
            return AgentOutput(
                intent="onboarding",
                extracted_fields=fields,
                missing_fields=[key for key in ("name", "business_name") if not merged.get(key)],
                proposed_reply_draft="Please share your name and business name.",
                requested_action=AgentAction.ASK_ONBOARDING_INFO,
            )

        missing_meeting = [
            key for key in ("meeting_date", "meeting_time", "location") if not merged.get(key)
        ]
        if missing_meeting:
            return AgentOutput(
                intent="meeting_request",
                extracted_fields=fields,
                missing_fields=missing_meeting,
                proposed_reply_draft=f"Please share your {missing_meeting[0].replace('_', ' ')}.",
                requested_action=AgentAction.ASK_MEETING_DETAILS,
            )

        return AgentOutput(
            intent="meeting_request",
            extracted_fields=fields,
            missing_fields=[],
            proposed_reply_draft="Please confirm these meeting details.",
            requested_action=AgentAction.REQUEST_CONFIRMATION,
        )
