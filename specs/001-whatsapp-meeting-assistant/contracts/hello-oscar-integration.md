# Contract: Hello Oscar Integration Adapter (structural only)

**This document intentionally does NOT define Hello Oscar's real endpoints, authentication, or wire
schemas.** Per the spec's External Integration Requirements and Constitution Principle IV, those details
must be supplied and approved separately. This document defines only the internal adapter shape the rest
of the system depends on, so the Booking Service can be built and tested against a stub today.

## Internal adapter interface

```python
from typing import Protocol, Literal, Union
from pydantic import BaseModel

class HelloOscarBookingRequest(BaseModel):
    booking_attempt_id: str   # idempotency key (research.md item 5)
    customer_name: str
    business_name: str
    meeting_date: str          # ISO date
    meeting_time: str          # ISO time
    location: str

class HelloOscarConfirmed(BaseModel):
    status: Literal["confirmed"]
    external_booking_id: str

class HelloOscarFailed(BaseModel):
    status: Literal["failed"]
    reason: str

class HelloOscarUnresolved(BaseModel):
    status: Literal["unresolved"]
    reason: str

HelloOscarBookingResult = Union[HelloOscarConfirmed, HelloOscarFailed, HelloOscarUnresolved]

class HelloOscarClient(Protocol):
    async def create_booking(self, request: HelloOscarBookingRequest) -> HelloOscarBookingResult: ...
```

## Required behaviors (structural, contract-agnostic)

- **Authentication**: adapter reads credentials from backend server-side configuration/secret storage
  only. NEEDS CLARIFICATION: actual auth scheme (API key, OAuth, mTLS, etc.).
- **Timeout**: adapter enforces a configurable request timeout; on timeout, returns `{status:
  'unresolved', reason: 'timeout'}` — never `'confirmed'`.
- **Retry**: NEEDS CLARIFICATION whether Hello Oscar is safe to retry on network failure; until
  confirmed, the adapter does NOT automatically retry `create_booking` (a retry could create a duplicate
  external booking without a confirmed idempotency-key contract). The Booking Service instead surfaces
  `unresolved` for reconciliation.
- **Reconciliation**: NEEDS CLARIFICATION what mechanism (polling endpoint, webhook, manual admin action)
  resolves an `unresolved` result to a final `confirmed`/`failed` state. Until defined, `UNRESOLVED`
  bookings require manual reconciliation support (e.g. an internal admin-only action, not exposed in the
  MVP dashboard scope defined by this request).
- **External booking identifier**: stored verbatim in `Booking.externalBookingId` only when
  `status: 'confirmed'`.
- **Error handling**: any non-2xx / malformed response from Hello Oscar maps to `'failed'` (if
  authoritatively rejected) or `'unresolved'` (if the outcome cannot be determined), never silently
  treated as success.

## Explicit exclusions (architecture boundary)

- The React frontend MUST NOT hold a reference to this client, its request/response types, or any
  Hello Oscar credential. All Hello Oscar interaction is backend-only, invoked exclusively from the
  Booking Service during `BOOKING_IN_PROGRESS` processing.
- The LangChain agent MUST NOT call this client directly; it can only request that the Booking Service
  attempt a booking, after the Business Rules layer has validated explicit confirmation.

## Traceability

External Integration Requirements (Hello Oscar), FR-008–FR-012, FR-025, NFR-002, Constitution II & IV.
