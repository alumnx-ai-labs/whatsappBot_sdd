import phonenumbers

from app.shared.config import settings


class InvalidPhoneNumberError(ValueError):
    pass


def normalize_phone(raw_phone: str) -> str:
    """Normalize any accepted input format to canonical E.164 (e.g. '+919494151816')."""
    candidate = raw_phone.strip()
    if not candidate:
        raise InvalidPhoneNumberError("phone number is empty")

    default_region = None if candidate.startswith("+") else settings.default_phone_country
    try:
        parsed = phonenumbers.parse(candidate, default_region)
    except phonenumbers.NumberParseException as exc:
        raise InvalidPhoneNumberError(f"could not parse phone number: {raw_phone}") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneNumberError(f"not a valid phone number: {raw_phone}")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
