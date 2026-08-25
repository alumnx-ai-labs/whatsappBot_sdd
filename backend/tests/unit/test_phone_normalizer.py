import pytest

from app.webhook.phone_normalizer import InvalidPhoneNumberError, normalize_phone


@pytest.mark.parametrize(
    "raw",
    ["+919494151816", "919494151816", "+91 94941 51816"],
)
def test_normalizes_equivalent_formats_identically(raw: str) -> None:
    assert normalize_phone(raw) == "+919494151816"


def test_rejects_empty_phone() -> None:
    with pytest.raises(InvalidPhoneNumberError):
        normalize_phone("")


def test_rejects_malformed_phone() -> None:
    with pytest.raises(InvalidPhoneNumberError):
        normalize_phone("not-a-phone")
