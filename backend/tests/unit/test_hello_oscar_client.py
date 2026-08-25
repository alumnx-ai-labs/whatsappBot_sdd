import pytest

from app.integrations.hello_oscar.hello_oscar_client import (
    HelloOscarClient,
    HelloOscarRequest,
    StubHelloOscarClient,
)


@pytest.mark.asyncio
async def test_stub_success_returns_external_booking_id() -> None:
    client = StubHelloOscarClient(result={"status": "confirmed", "external_booking_id": "HO-1"})
    result = await client.create_booking(HelloOscarRequest(booking_attempt_id="attempt-1"))
    assert result.status == "confirmed"
    assert result.external_booking_id == "HO-1"


@pytest.mark.asyncio
async def test_default_client_without_contract_is_unresolved() -> None:
    client = HelloOscarClient()
    result = await client.create_booking(HelloOscarRequest(booking_attempt_id="attempt-1"))
    assert result.status == "unresolved"


@pytest.mark.asyncio
async def test_stub_failure_never_confirms() -> None:
    client = StubHelloOscarClient(result={"status": "failed", "reason": "rejected"})
    result = await client.create_booking(HelloOscarRequest(booking_attempt_id="attempt-1"))
    assert result.status == "failed"
