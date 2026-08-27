from datetime import date

from app.agent.langchain_agent import LangChainAgent


def test_complete_iso_message_has_no_missing_fields() -> None:
    result = LangChainAgent().invoke(
        text="Book a meeting on 2099-09-01 at 14:30 at Downtown Office",
        context={"name": "Jane", "business_name": "Acme"},
    )

    assert result.missing_fields == []
    assert result.extracted_fields == {
        "meeting_date": "2099-09-01",
        "meeting_time": "14:30",
        "location": "Downtown Office",
    }


def test_complete_natural_language_message_has_no_follow_up_fields() -> None:
    result = LangChainAgent().invoke(
        text="I need a meeting tomorrow at 2pm at the Main Office",
        context={"name": "Jane", "business_name": "Acme"},
    )

    assert result.missing_fields == []
    assert result.extracted_fields["meeting_time"] == "2pm"
    assert result.extracted_fields["location"] == "the Main Office"


def test_schedule_appointment_message_has_no_follow_up_fields() -> None:
    result = LangChainAgent().invoke(
        text="Schedule an appointment tomorrow at 2pm at the Main Office",
        context={"name": "Jane", "business_name": "Acme"},
    )

    assert result.missing_fields == []
    assert result.extracted_fields["meeting_time"] == "2pm"
    assert result.extracted_fields["location"] == "the Main Office"


def test_meet_message_with_weekday_has_no_follow_up_fields() -> None:
    result = LangChainAgent().invoke(
        text="Can we meet Friday at 10:00 AM in Conference Room A",
        context={"name": "Jane", "business_name": "Acme"},
    )

    assert result.missing_fields == []
    assert result.extracted_fields["meeting_time"] == "10:00am"
    assert result.extracted_fields["location"] == "Conference Room A"


def test_relative_date_uses_business_timezone(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.agent.langchain_agent._business_today",
        lambda: date(2099, 12, 31),
    )
    result = LangChainAgent().invoke(
        text="meeting tomorrow at 10am at Office",
        context={"name": "Jane", "business_name": "Acme"},
    )

    assert result.extracted_fields["meeting_date"] == "2100-01-01"


def test_existing_context_is_preserved_when_message_contains_all_details() -> None:
    result = LangChainAgent().invoke(
        text="on 2099-09-01 at 11:00 in Conference Room A",
        context={
            "name": "Jane",
            "business_name": "Acme",
            "meeting_date": "2099-08-31",
        },
    )

    assert result.missing_fields == []
    assert result.extracted_fields["meeting_date"] == "2099-09-01"
    assert result.extracted_fields["location"] == "Conference Room A"
