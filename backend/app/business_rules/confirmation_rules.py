import re

_CONFIRMATION_PATTERN = re.compile(
    r"\b(yes|confirm|confirmed|book(?: it| this)?|go ahead|proceed)\b", re.IGNORECASE
)
_AMBIGUOUS_PATTERN = re.compile(r"\b(maybe|perhaps|sounds good|okay|ok|fine)\b", re.IGNORECASE)


def is_explicit_confirmation(text: str) -> bool:
    return bool(_CONFIRMATION_PATTERN.search(text)) and not is_ambiguous_confirmation(text)


def is_ambiguous_confirmation(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    return bool(_AMBIGUOUS_PATTERN.search(normalized)) and not bool(
        re.search(r"\b(yes|confirm|book|proceed)\b", normalized)
    )
