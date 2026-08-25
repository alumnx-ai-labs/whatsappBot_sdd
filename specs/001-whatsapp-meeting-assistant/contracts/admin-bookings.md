# Contract: Admin Bookings API

Owner: Backend Admin API. Consumed only by the React Admin Dashboard's Confirmed Bookings view.
Read-only — this API never triggers a booking, never calls Hello Oscar, never runs the LangChain agent.

## `GET /admin/bookings?status=CONFIRMED`

Requires a valid admin session (see admin-auth.md).

Query defaults to `status=CONFIRMED` when omitted; the dashboard's Confirmed Bookings view MUST always
request `CONFIRMED` explicitly so that filtering happens server-side (Constitution XX — reliable booking
visibility, not client-side filtering of a larger set).

**Response (200)**:
```json
{
  "bookings": [
    {
      "id": "uuid",
      "customerName": "Jane Doe",
      "businessName": "Acme Corp",
      "meetingDate": "2026-09-01",
      "meetingTime": "14:30",
      "location": "Downtown Office",
      "status": "CONFIRMED",
      "externalBookingId": "HO-12345",
      "createdAt": "2026-08-24T10:15:00Z",
      "updatedAt": "2026-08-24T10:16:00Z"
    }
  ],
  "total": 1
}
```

**Response (empty, 200)**:
```json
{ "bookings": [], "total": 0 }
```
Frontend renders an explicit empty state ("No confirmed bookings yet"), not a blank screen.

**Response (error, 5xx or 4xx)**:
```json
{ "error": "booking_fetch_failed" }
```
Frontend renders an explicit error state with a retry action.

## `GET /admin/bookings/:id`

Returns full detail for a single booking (used if the dashboard needs a detail view beyond the list row).
Returns `404` with `{ "error": "not_found" }` if the booking does not exist or does not belong to a
readable set.

## Refresh semantics

"Refresh" (FR-021) is implemented as the frontend re-invoking `GET /admin/bookings?status=CONFIRMED` on
demand (manual refresh button) — no separate backend endpoint is required. The frontend MUST show a
loading indicator during refresh and preserve the previous list until the new response arrives (avoid a
flash-to-empty state).

## Traceability

FR-020, FR-021, FR-022, User Story 4, Constitution XX.
