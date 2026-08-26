from datetime import date, timedelta

import pytest

from app.business_rules.meeting_validation import MeetingValidationError, validate_meeting_context


def valid_context() -> dict[str, str]:
    return {
        "meeting_date": (date.today() + timedelta(days=1)).isoformat(),
        "meeting_time": "2pm",
        "location": "Office",
    }


def test_accepts_valid_context() -> None:
    validate_meeting_context(valid_context())


@pytest.mark.parametrize(
    "field,value",
    [("meeting_date", "yesterday"), ("meeting_time", "99pm"), ("location", "")],
)
def test_rejects_invalid_context(field: str, value: str) -> None:
    context = valid_context()
    if field == "meeting_date":
        context[field] = (date.today() - timedelta(days=1)).isoformat()
    else:
        context[field] = value
    with pytest.raises(MeetingValidationError):
        validate_meeting_context(context)
