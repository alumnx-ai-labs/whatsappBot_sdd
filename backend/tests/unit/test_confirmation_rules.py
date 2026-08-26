import pytest

from app.business_rules.confirmation_rules import (
    is_ambiguous_confirmation,
    is_explicit_confirmation,
)


@pytest.mark.parametrize("text", ["yes", "Yes, confirm", "please book it", "confirmed"])
def test_accepts_explicit_confirmation(text: str) -> None:
    assert is_explicit_confirmation(text) is True


@pytest.mark.parametrize("text", ["maybe", "sounds good", "what about 3pm", "no"])
def test_rejects_non_confirmation(text: str) -> None:
    assert is_explicit_confirmation(text) is False


def test_identifies_ambiguous_reply() -> None:
    assert is_ambiguous_confirmation("sounds good") is True
    assert is_ambiguous_confirmation("yes please confirm") is False
