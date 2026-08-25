from sqlalchemy.orm import Session

from app.db.models import ConversationSession, InboundMessage


def test_generic_greeting_without_active_session_is_not_handled(client) -> None:
    response = client.post(
        "/webhook-sync",
        json={"phone": "+919494151816", "text": "hello", "message_id": "hello-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"handled": False}


def test_raw_skalebot_payload_is_normalized(client) -> None:
    response = client.post(
        "/webhook-sync",
        json={
            "query": "hello",
            "callback": "",
            "mediaUrl": "",
            "phoneNumber": "919494151816",
        },
        headers={"X-Provider-Delivery-Id": "raw-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"handled": False}


def test_invalid_phone_returns_bad_request(client) -> None:
    response = client.post(
        "/webhook-sync",
        json={"phone": "not-a-phone", "text": "hello", "message_id": "bad-1"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_payload"


def test_duplicate_message_replays_original_response(client, test_db_engine) -> None:
    payload = {"phone": "+919494151816", "text": "hello", "message_id": "duplicate-1"}
    first = client.post("/webhook-sync", json=payload)
    second = client.post("/webhook-sync", json=payload)

    assert first.json() == {"handled": False}
    assert second.json() == first.json()
    with Session(test_db_engine) as db:
        assert db.query(InboundMessage).filter_by(message_id="duplicate-1").count() == 1
        assert db.query(ConversationSession).count() == 0
