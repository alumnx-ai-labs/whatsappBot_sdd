from hashlib import sha256
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class PayloadNormalizationError(ValueError):
    pass


class NormalizedInboundMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    phone: str
    text: str
    message_id: str = Field(min_length=1)


def _derived_message_id(payload: dict[str, Any], provider_delivery_id: str | None) -> str:
    if provider_delivery_id:
        return f"derived:{provider_delivery_id}"

    content = f"{payload.get('phoneNumber', '')}\0{payload.get('query', '')}"
    return f"derived:{sha256(content.encode('utf-8')).hexdigest()}"


def normalize_payload(
    payload: Any, provider_delivery_id: str | None = None
) -> NormalizedInboundMessage:
    if not isinstance(payload, dict):
        raise PayloadNormalizationError("payload must be a JSON object")

    is_normalized = {"phone", "text", "message_id"}.issubset(payload)
    is_skalebot = "query" in payload and "phoneNumber" in payload

    if not is_normalized and not is_skalebot:
        raise PayloadNormalizationError(
            "payload must contain phone, text, message_id or query and phoneNumber"
        )

    try:
        if is_normalized:
            return NormalizedInboundMessage(
                phone=payload["phone"],
                text=payload["text"],
                message_id=payload["message_id"],
            )

        return NormalizedInboundMessage(
            phone=payload["phoneNumber"],
            text=payload["query"],
            message_id=_derived_message_id(payload, provider_delivery_id),
        )
    except (KeyError, TypeError, ValidationError) as exc:
        raise PayloadNormalizationError("payload fields must be non-empty strings") from exc
