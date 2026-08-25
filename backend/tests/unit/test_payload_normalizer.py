import pytest

from app.webhook.payload_normalizer import PayloadNormalizationError, normalize_payload


def test_normalized_payload_maps_to_internal_contract() -> None:
    result = normalize_payload(
        {
            "phone": "+919494151816",
            "text": "Hello Oscar",
            "message_id": "message-1",
        }
    )

    assert result.phone == "+919494151816"
    assert result.text == "Hello Oscar"
    assert result.message_id == "message-1"


def test_raw_skalebot_payload_maps_fields_and_derives_id() -> None:
    result = normalize_payload(
        {
            "query": "hi",
            "callback": "",
            "mediaUrl": "",
            "phoneNumber": "919494151816",
        }
    )

    assert result.phone == "919494151816"
    assert result.text == "hi"
    assert result.message_id.startswith("derived:")


def test_provider_delivery_id_makes_raw_id_stable() -> None:
    payload = {"query": "hi", "phoneNumber": "919494151816"}
    first = normalize_payload(payload, provider_delivery_id="delivery-1")
    second = normalize_payload(payload, provider_delivery_id="delivery-1")

    assert first.message_id == second.message_id


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"phone": "+919494151816", "text": "hi"},
        {"query": "hi"},
        {"phone": "+919494151816", "text": 123, "message_id": "id"},
    ],
)
def test_invalid_payload_raises(payload: dict) -> None:
    with pytest.raises(PayloadNormalizationError):
        normalize_payload(payload)
