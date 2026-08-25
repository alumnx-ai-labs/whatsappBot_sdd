from datetime import date

from langchain.tools import tool


@tool
def identify_missing_onboarding_fields(name: str | None, business_name: str | None) -> list[str]:
    """Return onboarding fields that are still missing; does not write to storage."""
    return [
        field
        for field, value in (("name", name), ("business_name", business_name))
        if not value or not value.strip()
    ]


@tool
def validate_meeting_date(meeting_date: str) -> bool:
    """Return whether an ISO meeting date is today or in the future."""
    try:
        return date.fromisoformat(meeting_date) >= date.today()
    except ValueError:
        return False


@tool
def identify_missing_meeting_fields(
    meeting_date: str | None, meeting_time: str | None, location: str | None
) -> list[str]:
    """Return missing meeting fields; does not book or mutate a record."""
    return [
        field
        for field, value in (
            ("meeting_date", meeting_date),
            ("meeting_time", meeting_time),
            ("location", location),
        )
        if not value or not value.strip()
    ]


TOOLS = [
    identify_missing_onboarding_fields,
    validate_meeting_date,
    identify_missing_meeting_fields,
]
