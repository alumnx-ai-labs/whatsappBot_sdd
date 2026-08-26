GENERIC_GREETINGS = frozenset({"hi", "hello", "hie"})
ROUTING_TRIGGERS = frozenset({"hello oscar"})


def is_owned_message(*, text: str, has_active_session: bool) -> bool:
    if has_active_session:
        return True

    normalized_text = " ".join(text.casefold().split())
    if normalized_text in GENERIC_GREETINGS:
        return False

    return normalized_text in ROUTING_TRIGGERS
