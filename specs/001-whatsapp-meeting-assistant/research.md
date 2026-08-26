# Phase 0 Research: WhatsApp Meeting Assistant

## 1. Backend/frontend language and framework

- **Decision**: Python 3.11+ with FastAPI + Uvicorn for the backend; React 18 + Vite + TypeScript for
  the frontend (unchanged, separate runtime).
- **Rationale**: Explicit requirement for this revision: use Python FastAPI and LangChain for the
  backend. `langchain` (Python) is the reference implementation with the broadest tool/agent/community
  support, and FastAPI's native Pydantic integration gives the same request/response validation rigor
  that a TypeScript+Zod stack would have provided. The frontend remains a fully separate application
  with its own runtime, so using a different language there does not reintroduce any shared-code
  coupling or violate the frontend/backend architecture boundary.
- **Alternatives considered**: Node.js/TypeScript + Express backend (the prior revision's choice) —
  superseded by this explicit instruction; LangChain.js is equally capable but is no longer the selected
  path. Django/DRF — rejected as heavier than needed for a single-service MVP with no admin-site
  requirements beyond the defined API surface; FastAPI's async support also fits webhook-style I/O
  better.

## 2. Persistence

- **Decision**: SQLite as a single local database file (e.g. `backend/data/app.db`), accessed through
  SQLAlchemy 2.x models and Alembic migrations.
- **Rationale**: Explicit requirement for this revision: a simple local database, avoiding the
  operational overhead of running a separate PostgreSQL server for the MVP. SQLite still enforces the
  `UNIQUE` constraints this feature depends on (canonical phone number, `message_id`, `bookingAttemptId`)
  and supports transactions for atomic state transitions, which covers NFR-001/NFR-002's integrity
  needs at MVP scale. SQLAlchemy + Alembic keep the schema/migration workflow structured so a later move
  to PostgreSQL (if concurrency/scale requires it) only changes the connection string and dialect, not
  the application code.
- **Alternatives considered**: PostgreSQL (the prior revision's choice) — superseded by this explicit
  "simple local database" instruction; remains the documented upgrade path if concurrent-write volume or
  multi-instance deployment later requires it. MongoDB — still rejected for the same reason as before:
  weaker native uniqueness/transactional guarantees for idempotency and state transitions.
- **Operational note**: SQLite has known limits under high write concurrency (single-writer locking).
  This is acceptable for the stated MVP scope (single-tenant, one shared WhatsApp number) but should be
  re-evaluated if traffic grows; `NEEDS CLARIFICATION`: confirm expected concurrent webhook volume before
  release to validate SQLite remains sufficient.

## 3. Admin authentication mechanism

- **Decision**: Backend-issued, HttpOnly, Secure, SameSite=Strict session cookie, signed with
  `itsdangerous` (or a JWT signed with `PyJWT`, stored only in an HttpOnly cookie) issued by
  `POST /admin/auth/login`. Passwords hashed with `passlib[bcrypt]`.
- **Rationale**: Spec assumption states "the authentication mechanism remains to be selected" — a single
  administrator role with no client-visible token satisfies NFR-003 (credentials outside user-facing
  clients) and is simplest to reason about for logout/session invalidation. FastAPI has first-class
  support for cookie-based dependencies (`Depends`) to protect admin routers.
- **Alternatives considered**: Storing a JWT in `localStorage` — rejected, vulnerable to XSS token theft
  and conflicts with NFR-003's "credentials MUST remain outside user-facing clients" language in spirit
  (a stolen admin token is equivalent to a credential).
- **Open item**: Whether administrators are single, hardcoded, or backed by an `admin_users` table with
  hashed passwords must be confirmed before implementation; plan assumes an `AdminUser` table with
  bcrypt-hashed passwords as the default, simplest approach consistent with "single administrator role."

## 4. Message idempotency mechanism

- **Decision**: An `InboundMessage` table with a unique constraint on (canonical phone number,
  `message_id`) or globally unique `message_id` if SkaleBot guarantees global uniqueness. On receipt,
  the webhook handler attempts an insert-first-if-absent; if the row already exists, the handler returns
  the previously computed response (stored alongside the message row) without re-invoking the agent or
  booking service.
- **Rationale**: Directly satisfies FR-013/NFR-001 and the spec's edge case "processing is idempotent
  and does not duplicate records or bookings." Storing the prior response also guarantees identical
  replies to identical retries (no inconsistent responses).
- **Alternatives considered**: Redis-based dedupe cache with TTL — rejected as primary mechanism because
  it would not durably prevent duplicate bookings if the cache entry expires before a delayed retry;
  could be layered later purely as a request-rate optimization, not as the source of truth.

## 5. Booking idempotency toward Hello Oscar

- **Decision**: Each booking attempt carries a stable idempotency key derived from the conversation's
  `booking_attempt_id` (a UUID generated once when a proposal enters `BOOKING_IN_PROGRESS`). The Hello
  Oscar adapter is required (once its contract is approved) to either support idempotency keys directly
  or the adapter enforces "one call per booking_attempt_id" locally via a unique constraint before
  dispatching the request.
- **Rationale**: Prevents duplicate external bookings from a repeated internal retry, independent of
  whether Hello Oscar itself supports idempotency keys.
- **NEEDS CLARIFICATION**: Whether Hello Oscar's API natively accepts an idempotency key/header. Deferred
  to the approved Hello Oscar contract (see item 9).

## 6. Phone number normalization

- **Decision**: Canonical format is E.164 without spaces (e.g. `+919494151816`). Normalization applies a
  library (e.g. `libphonenumber-js`) with a configured default country (India, `IN`) fallback when a
  number arrives without a leading `+` (e.g. raw SkaleBot `"919949014298"`), and strips spaces/punctuation
  before parsing.
- **Rationale**: Directly matches the examples given (`+919494151816`, `919949014298`, `+91 94941
  51816` all must normalize identically) and E.164 is the standard canonical WhatsApp identifier format.
- **Alternatives considered**: Storing raw strings and normalizing per-query — rejected; normalizing once
  at ingestion keeps all downstream lookups (visitor, customer, session, duplicate detection) simple
  equality checks against one canonical column.

## 7. Payload normalization (approved contract vs. raw SkaleBot format)

- **Decision**: A single `PayloadNormalizer` accepts either shape and maps to one internal
  `NormalizedInboundMessage { phone, text, messageId }`:
  - Approved contract: `{ phone, text, message_id }` → direct passthrough (with phone normalization).
  - Raw SkaleBot: `{ query, callback, mediaUrl, phoneNumber }` → `text = query`, `phone = phoneNumber`.
    Since raw SkaleBot payloads shown do not include a `message_id`, the normalizer MUST derive a stable
    idempotency key when absent (e.g. hash of `phoneNumber + query + a provider-supplied delivery id` if
    available, else a hash of `phoneNumber + query + inbound timestamp bucket` as a best-effort fallback)
    — flagged as **NEEDS CLARIFICATION**: confirm whether SkaleBot's real webhook delivery includes any
    stable delivery/message identifier (header or body field) not shown in the sample payload, since a
    fully synthetic key based on content+time cannot guarantee the same duplicate-safety as a real
    provider message id.
- **Rationale**: Keeps a single internal contract for every downstream service; only the normalizer needs
  to know about provider-specific payload shapes.

## 8. Message ownership detection ("shared number" rule)

- **Decision**: Ownership is granted (`handled: true`) only when at least one of:
  1. An active, non-expired `ConversationSession` already exists for the canonical phone number and was
     created/last touched by this bot, or
  2. The inbound text matches an explicit, approved routing trigger for this bot (e.g. a specific
     onboarding/menu keyword or deep-link code documented in the approved WhatsApp integration contract,
     not yet defined in this spec) — **NEEDS CLARIFICATION**: the exact trigger phrase(s)/keyword(s) that
     signal "this message is for the Meeting Assistant bot" on a shared number must be supplied and
     approved; until then, only rule 1 (existing active session) is implemented, and generic greetings
     with no active session always return `handled: false` per the spec's explicit requirement.
- **Rationale**: Matches the explicit instruction that generic greetings ("hi", "hello", "hie") must never
  be auto-claimed without an active session or an approved routing trigger.

## 9. Hello Oscar integration contract

- **Decision**: Do not invent endpoints, auth scheme, or schemas. Plan only the adapter's structural
  shape: `HelloOscarClient.createBooking(request): Promise<HelloOscarResult>`, where `HelloOscarResult`
  is a discriminated union of `{status: 'confirmed', externalBookingId} | {status: 'failed', reason} |
  {status: 'unresolved', reason}`, plus configurable timeout and a documented (not yet implemented)
  retry policy.
- **NEEDS CLARIFICATION** (blocking full adapter implementation, per spec's External Integration
  Requirements): base URL, authentication mechanism, endpoint paths, request/response schemas,
  availability-check behavior, error response shapes, timezone handling, external booking identifier
  field name, cancellation/rescheduling endpoints, timeout defaults, retry policy, and reconciliation
  endpoint/webhook for resolving `UNRESOLVED` outcomes.
- **Rationale**: Constitution Principle IV and the spec explicitly forbid inventing this contract; the
  plan isolates the unknown behind one adapter so the rest of the system can be built and tested against
  a stub/mock implementing the same interface.

## 10. CSV upload processing model

- **Decision**: Synchronous request/response processing for the MVP (parse → validate every row →
  persist accepted rows → return a full per-row report) rather than an async job with polling, given
  expected metadata file sizes are small (business/customer records, not high-volume transactional data).
  Upload endpoint enforces a maximum file size and row count (exact numbers to be set as a config
  constant, defaulting conservatively, e.g. 5MB / 5,000 rows) documented in the CSV contract.
- **Rationale**: Matches "default assumption is partial success with an explicit result report and no
  silent row loss" without needing background job infrastructure for MVP scope (Principle X, minimal
  scope).
- **Alternatives considered**: Background job + polling/webhook for large files — deferred; can be added
  later without changing the admin API's external contract shape (report structure stays the same).

## 11. LangChain agent boundary and tool design

- **Decision**: The agent is invoked per-turn with the current conversation state (visitor known/unknown,
  collected fields, current booking state) and returns a single structured object matching a Zod schema:
  `{ intent, extractedFields, missingFields, proposedReplyDraft, requestedAction }` where
  `requestedAction` is one of a closed enum (`ASK_ONBOARDING_INFO | ASK_MEETING_DETAILS |
  PRESENT_PROPOSAL | REQUEST_CONFIRMATION | NONE`). The agent never calls a "confirm booking" or "create
  booking" tool directly — those actions live only in the deterministic Business Rules / Booking Service
  layer, which decides whether to act on the agent's `requestedAction` after independently validating
  state and confirmation status.
- **Rationale**: Satisfies Constitution XVII (AI cannot override business rules) and the explicit
  instruction that the LangChain agent must not directly mark a booking confirmed; the agent proposes,
  the deterministic layer disposes.

## 12. Conversation session lifecycle & silent expiry

- **Decision**: `ConversationSession.updatedAt` plus a configurable `PROPOSAL_EXPIRY_MINUTES` constant
  (exact value **NEEDS CLARIFICATION** — spec says "defined period" without a number). A scheduled sweep
  (cron/interval job) or lazy check-on-read (compare `now - updatedAt` against the threshold whenever the
  session is loaded) transitions any session stuck in `CONFIRMATION_PENDING`/`PROPOSED` past the
  threshold directly to an expired/closed sub-state, with no outbound message sent.
- **Rationale**: Lazy check-on-read avoids needing a background scheduler for MVP while still guaranteeing
  no stale proposal can be confirmed after expiry (checked before accepting any confirmation).

## 13. Testing tools

- **Decision**: Pytest for backend unit and integration tests, FastAPI's `TestClient` (httpx-based) for
  HTTP contract tests, React Testing Library + Vitest for frontend component tests. No end-to-end/
  browser-automation suite (e.g. Playwright) is used — explicitly descoped for this MVP.
- **Rationale**: Pytest + `TestClient` are the standard, idiomatic choice for FastAPI services and need
  no additional language runtime. Integration tests against the `TestClient` plus a stubbed Hello Oscar
  server already exercise the full webhook-to-booking flow, so a separate e2e suite was judged
  unnecessary overhead for the MVP scope.

## Summary of open NEEDS CLARIFICATION items carried into implementation

1. Hello Oscar full contract (base URL, auth, endpoints, schemas, timeout/retry, reconciliation) — item 9.
2. Exact shared-number bot-ownership trigger(s) beyond "existing active session" — item 8.
3. Whether raw SkaleBot webhook delivery includes any real stable message/delivery identifier — item 7.
4. Numeric value for proposal silent-expiry duration — item 12.
5. Administrator account provisioning model (fixed single account vs. `admin_users` table) — item 3.
6. Maximum CSV file size / row count limits — item 10.
7. Expected concurrent webhook write volume, to confirm SQLite's single-writer locking remains
   sufficient for the MVP — item 2.

These are documented, not invented, per Constitution Principle IV and the spec's explicit prohibition on
inventing the Hello Oscar contract. Downstream design (data-model.md, contracts/) is built so that
resolving these items later does not require restructuring the system.
