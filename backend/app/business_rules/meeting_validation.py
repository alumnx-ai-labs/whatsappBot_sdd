import re
from datetime import date

from app.shared.config import settings

_TIME_PATTERN = re.compile(r"^(?:[01]?\d|2[0-3])(?::[0-5]\d)?(?:\s?(?:am|pm))?$", re.I)


class MeetingValidationError(ValueError):
    pass


def validate_meeting_context(context: dict) -> None:
    required = ("meeting_date", "meeting_time", "location")
    missing = [field for field in required if not str(context.get(field, "")).strip()]
    if missing:
        raise MeetingValidationError(f"Missing required meeting fields: {', '.join(missing)}")

    try:
        meeting_date = date.fromisoformat(str(context["meeting_date"]))
    except ValueError as exc:
        raise MeetingValidationError("meeting_date must be an ISO date") from exc
    if meeting_date < date.today():
        raise MeetingValidationError("meeting_date cannot be in the past")

    meeting_time = str(context["meeting_time"]).strip()
    if not _TIME_PATTERN.fullmatch(meeting_time):
        raise MeetingValidationError("meeting_time must be a valid 12-hour or 24-hour time")

    allowed_locations = {
        item.strip().casefold() for item in settings.supported_locations.split(",") if item.strip()
    }
    if allowed_locations and str(context["location"]).strip().casefold() not in allowed_locations:
        raise MeetingValidationError("location is not supported")
