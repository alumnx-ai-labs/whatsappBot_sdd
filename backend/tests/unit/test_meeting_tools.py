from app.agent.tools.meeting_tools import (
    identify_missing_meeting_fields,
    identify_missing_onboarding_fields,
    validate_meeting_date,
)


def test_tools_are_read_only_validation_helpers() -> None:
    assert identify_missing_onboarding_fields.invoke({"name": "Jane", "business_name": None}) == [
        "business_name"
    ]
    assert identify_missing_meeting_fields.invoke(
        {"meeting_date": "2026-09-01", "meeting_time": None, "location": "Office"}
    ) == ["meeting_time"]
    assert validate_meeting_date.invoke({"meeting_date": "not-a-date"}) is False
