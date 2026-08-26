import pytest

from app.webhook.ownership_detector import is_owned_message


@pytest.mark.parametrize("text", ["hi", "hello", "hie", " Hello "])
def test_generic_greeting_without_session_is_not_owned(text: str) -> None:
    assert is_owned_message(text=text, has_active_session=False) is False


def test_active_session_owns_generic_greeting() -> None:
    assert is_owned_message(text="hello", has_active_session=True) is True


def test_active_session_owns_any_text() -> None:
    assert is_owned_message(text="I need a meeting", has_active_session=True) is True


def test_unmatched_new_message_is_not_owned_without_trigger() -> None:
    assert is_owned_message(text="I need a meeting", has_active_session=False) is False


def test_hello_oscar_routes_a_new_visitor() -> None:
    assert is_owned_message(text="Hello Oscar", has_active_session=False) is True
