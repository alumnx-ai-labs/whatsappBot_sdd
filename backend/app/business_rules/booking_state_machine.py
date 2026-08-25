from enum import StrEnum


class BookingState(StrEnum):
    PROPOSED = "PROPOSED"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING"
    BOOKING_IN_PROGRESS = "BOOKING_IN_PROGRESS"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNRESOLVED = "UNRESOLVED"


class InvalidTransition(ValueError):
    pass


_TRANSITIONS: dict[tuple[BookingState, str], BookingState] = {
    (BookingState.PROPOSED, "details_complete"): BookingState.CONFIRMATION_PENDING,
    (BookingState.CONFIRMATION_PENDING, "explicit_confirmation"): BookingState.BOOKING_IN_PROGRESS,
    (BookingState.BOOKING_IN_PROGRESS, "provider_success"): BookingState.CONFIRMED,
    (BookingState.BOOKING_IN_PROGRESS, "provider_failure"): BookingState.FAILED,
    (BookingState.BOOKING_IN_PROGRESS, "provider_unknown"): BookingState.UNRESOLVED,
    (BookingState.UNRESOLVED, "provider_success"): BookingState.CONFIRMED,
    (BookingState.UNRESOLVED, "provider_failure"): BookingState.FAILED,
    (BookingState.CONFIRMED, "approved_cancellation"): BookingState.CANCELLED,
}


def transition(current: BookingState, event: str) -> BookingState:
    try:
        return _TRANSITIONS[(current, event)]
    except KeyError as exc:
        raise InvalidTransition(f"Cannot apply {event!r} in state {current.value}") from exc
