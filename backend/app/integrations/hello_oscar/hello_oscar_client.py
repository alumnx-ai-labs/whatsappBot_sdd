from typing import Literal

from pydantic import BaseModel

from app.shared.config import settings


class HelloOscarRequest(BaseModel):
    booking_attempt_id: str
    customer_name: str | None = None
    business_name: str | None = None
    meeting_date: str | None = None
    meeting_time: str | None = None
    location: str | None = None


class ConfirmedResult(BaseModel):
    status: Literal["confirmed"]
    external_booking_id: str


class FailedResult(BaseModel):
    status: Literal["failed"]
    reason: str


class UnresolvedResult(BaseModel):
    status: Literal["unresolved"]
    reason: str


HelloOscarResult = ConfirmedResult | FailedResult | UnresolvedResult


class HelloOscarClient:
    """Provider boundary; wire details remain disabled until the approved contract is supplied."""

    async def create_booking(self, request: HelloOscarRequest) -> HelloOscarResult:
        del request
        if not settings.hello_oscar_base_url:
            return UnresolvedResult(status="unresolved", reason="provider_contract_not_configured")
        return UnresolvedResult(status="unresolved", reason="provider_transport_not_implemented")


class StubHelloOscarClient(HelloOscarClient):
    def __init__(self, result: dict[str, str]) -> None:
        self.result = result

    async def create_booking(self, request: HelloOscarRequest) -> HelloOscarResult:
        del request
        if self.result["status"] == "confirmed":
            return ConfirmedResult.model_validate(self.result)
        if self.result["status"] == "failed":
            return FailedResult.model_validate(self.result)
        return UnresolvedResult.model_validate(self.result)
