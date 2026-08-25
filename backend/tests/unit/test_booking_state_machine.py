import pytest

from app.business_rules.booking_state_machine import BookingState, InvalidTransition, transition


def test_valid_booking_transitions() -> None:
    assert (
        transition(BookingState.PROPOSED, "details_complete") == BookingState.CONFIRMATION_PENDING
    )
    assert (
        transition(BookingState.CONFIRMATION_PENDING, "explicit_confirmation")
        == BookingState.BOOKING_IN_PROGRESS
    )
    assert (
        transition(BookingState.BOOKING_IN_PROGRESS, "provider_success") == BookingState.CONFIRMED
    )


@pytest.mark.parametrize(
    ("current", "event"),
    [
        (BookingState.PROPOSED, "provider_success"),
        (BookingState.CONFIRMATION_PENDING, "ambiguous_reply"),
        (BookingState.CONFIRMED, "provider_success"),
    ],
)
def test_invalid_booking_transitions_are_rejected(current: BookingState, event: str) -> None:
    with pytest.raises(InvalidTransition):
        transition(current, event)


def test_provider_failure_is_not_confirmation() -> None:
    assert transition(BookingState.BOOKING_IN_PROGRESS, "provider_failure") == BookingState.FAILED
    assert (
        transition(BookingState.BOOKING_IN_PROGRESS, "provider_unknown") == BookingState.UNRESOLVED
    )
