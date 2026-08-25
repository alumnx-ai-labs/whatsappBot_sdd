# Quickstart: WhatsApp Meeting Assistant

Validation guide for confirming the feature works end-to-end. This is not an implementation guide —
see `data-model.md` and `contracts/` for design details, and the future `tasks.md` for build steps.

## Prerequisites

- No separate database server required: the backend uses a local SQLite file (e.g. `backend/data/app.db`),
  created automatically by running migrations.
- Backend `.env` configured with: SQLite file path, admin session signing secret, Hello Oscar base URL +
  credentials (or a local stub server implementing `contracts/hello-oscar-integration.md`'s interface for
  pre-approval testing), LangChain/LLM provider API key.
- Python 3.11+ and `pip`/`venv` (or `poetry`) installed for `backend/`; Node.js 20+ installed for
  `frontend/`.
- A seeded `AdminUser` record (via seed script) to log into the dashboard.

## Setup

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head        # creates the local SQLite file and schema
python -m app.seed          # creates a test AdminUser + sample BusinessMetadata
uvicorn app.main:app --reload --port 8000   # starts the API + webhook server

# Frontend
cd frontend
npm install
npm run dev        # starts the React admin dashboard
```

## Scenario 1: Unrelated greeting is not claimed (shared number rule)

```bash
curl -X POST http://localhost:8000/webhook-sync \
  -H "Content-Type: application/json" \
  -d '{"phone":"+919999999999","text":"hi","message_id":"msg-001"}'
```
**Expected**: `{ "handled": false }` — no `ConversationSession` or `Customer` record is created for this
phone number (verify via DB or an internal debug query).

## Scenario 2: Raw SkaleBot payload is normalized correctly

```bash
curl -X POST http://localhost:8000/webhook-sync \
  -H "Content-Type: application/json" \
  -d '{"query":"I want to book a meeting for tomorrow at 3pm at the downtown office","callback":"","mediaUrl":"","phoneNumber":"919949014298"}'
```
**Expected**: request is accepted (`400` only if malformed); phone normalizes to `+919949014298`; if no
prior session exists and no approved routing trigger matches, response is `{ "handled": false }` per the
shared-number rule (documented limitation until routing triggers are approved — see research.md item 8).
Once an active session exists (e.g. after Scenario 3 begins), a follow-up message on the same phone
number returns `handled: true`.

## Scenario 3: New visitor completes onboarding and reaches a proposal

1. Send onboarding info via the normalized contract for a fresh phone number that already has an active
   session (simulate by first establishing session state through your test harness/seed, since a first
   message alone follows the shared-number rule above).
2. Send name + business name.
3. Send a complete meeting request ("Tuesday 2pm at Downtown Office").

**Expected**: final response's `reply` summarizes the proposed appointment and asks for explicit
confirmation; `ConversationSession.state = CONFIRMATION_PENDING`; no `Booking` row exists yet.

## Scenario 4: Explicit confirmation triggers Hello Oscar and reaches CONFIRMED

Send an explicit confirmation message (e.g. "yes, confirm").

**Expected** (against a stub Hello Oscar returning success): response reply states the meeting is
confirmed; `Booking.status = CONFIRMED`; `Booking.externalBookingId` populated; `BookingStateTransition`
rows show `PROPOSED → CONFIRMATION_PENDING → BOOKING_IN_PROGRESS → CONFIRMED`.

## Scenario 5: Hello Oscar failure never shows as confirmed

Repeat Scenario 4 against a stub Hello Oscar configured to return a failure/timeout.

**Expected**: reply states the booking was not confirmed and offers a recovery path;
`Booking.status = FAILED` or `UNRESOLVED`; dashboard's Confirmed Bookings view does not show this
booking.

## Scenario 6: Duplicate `message_id` is idempotent

Resend the exact request from Scenario 4 with the same `message_id`.

**Expected**: identical response returned; no new `Booking`, `ConversationSession`, or
`BookingStateTransition` rows created; only one `InboundMessage` row exists for that `message_id`.

## Scenario 7: Admin dashboard — confirmed bookings view

1. Log in at the dashboard's login page using the seeded `AdminUser` credentials.
2. Navigate to the Confirmed Bookings view.

**Expected**: the booking from Scenario 4 appears with customer/business name, date, time, location,
status, creation time. Trigger "Refresh" — list re-fetches from `GET /admin/bookings?status=CONFIRMED`
and reflects any newly confirmed booking. Log out; confirm the bookings view and API are no longer
accessible (`401`) after logout.

## Scenario 8: Metadata form validation

Submit the metadata form with a missing `businessName`. **Expected**: inline field error shown, no
network write persisted, submit blocked until corrected.

## Scenario 9: CSV upload with mixed valid/invalid rows

Upload a CSV containing one valid new row, one row updating an existing record, one row with an invalid
phone number, and one duplicate-within-file row.

**Expected**: response/report shows all four rows with `CREATED`, `UPDATED`, `REJECTED` (with reason),
and `SKIPPED` (with reason) respectively; dashboard renders a summary table matching the report; no row
is silently dropped.

## Pass/fail criteria

Quickstart passes when all nine scenarios produce the expected outcomes above without manual data
cleanup between runs failing subsequent scenarios (each scenario should be runnable against a freshly
seeded database).
