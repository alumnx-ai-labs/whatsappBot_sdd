# Phase 1 Data Model: WhatsApp Meeting Assistant

All entities are relational tables (SQLite local database file via SQLAlchemy models + Alembic
migrations). Timestamps are UTC. Traceability references back to spec.md Functional Requirements (FR-*)
and Data Requirements. `JSONB` below denotes a JSON-typed column (stored as SQLite's `JSON`/`TEXT`
affinity via SQLAlchemy's `JSON` type); `UUID` denotes a string primary key holding a UUID4 value (SQLite
has no native UUID type).

## Entity: Customer (Visitor)

Represents the unique WhatsApp visitor/business identified by phone number (FR-002, FR-003, Data
Requirements).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | Customer identifier |
| `canonicalPhone` | string | UNIQUE, NOT NULL | E.164 normalized (research item 6) |
| `name` | string | NOT NULL | Mandatory for new visitors (FR-003) |
| `businessName` | string | NOT NULL | Mandatory for new visitors |
| `contactInfo` | string | NULL | Optional unless required by workflow |
| `createdAt` | datetime | NOT NULL, default now | |
| `lastInteractionAt` | datetime | NOT NULL | Updated on every inbound message |

**Relationships**: one Customer → many ConversationSession, many Booking, many InboundMessage (via
canonical phone).

**Validation rules**: `canonicalPhone` must pass phone normalization; `name`/`businessName` required
before a Customer row is created (onboarding gate, FR-003).

## Entity: BusinessMetadata

Administrative business/customer metadata managed via single-entry form or CSV (FR-015–FR-019).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `businessName` | string | NOT NULL | |
| `contactPerson` | string | NOT NULL | |
| `whatsappPhone` | string | UNIQUE, NOT NULL | Canonical format; duplicate-detection key (FR-019) |
| `address` | string | NULL | |
| `sector` | string | NULL | |
| `businessDescription` | string | NULL | |
| `createdAt` | datetime | NOT NULL | |
| `updatedAt` | datetime | NOT NULL | |
| `sourceType` | enum(`FORM`,`CSV`) | NOT NULL | For audit/traceability |

**Validation rules**: required fields enforced server-side (never store invalid/incomplete rows, FR-016).
Duplicate policy keyed on `whatsappPhone`: existing match → update (or reported as skipped, per approved
duplicate policy); no match → create. Every write reports created/updated/skipped/rejected (FR-019).

**Relationship to Customer**: `BusinessMetadata.whatsappPhone` may correspond to a `Customer` record but
is modeled as an independent administrative table since metadata can be entered before any WhatsApp
conversation occurs (FR-015 supports proactive administrative entry).

## Entity: ConversationSession

Tracks an active or historical WhatsApp conversation (FR-001, Conversation and Session Management).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | Session identifier |
| `customerId` | UUID | FK → Customer, NULL until onboarding completes | Session may start before Customer exists |
| `canonicalPhone` | string | NOT NULL, INDEX | Primary lookup key even pre-onboarding |
| `state` | enum | NOT NULL | `ONBOARDING \| COLLECTING_MEETING_INFO \| PROPOSED \| CONFIRMATION_PENDING \| BOOKING_IN_PROGRESS \| CONFIRMED \| FAILED \| UNRESOLVED \| EXPIRED \| IDLE` |
| `isActive` | boolean | NOT NULL, default true | False once expired/closed/confirmed-terminal |
| `context` | JSONB | NOT NULL | Structured collected fields: onboarding answers, meeting date/time/location draft, last proposal summary |
| `activeBookingId` | UUID | FK → Booking, NULL | Set once a booking attempt is created for this session |
| `createdAt` | datetime | NOT NULL | |
| `updatedAt` | datetime | NOT NULL | Used for silent-expiry check (research item 12) |

**Validation rules / behavior**:
- Ownership detection (research item 8) reads `isActive=true` sessions by `canonicalPhone`.
- Lazy expiry check on every read: if `state` in (`PROPOSED`,`CONFIRMATION_PENDING`) and
  `now - updatedAt > PROPOSAL_EXPIRY_MINUTES`, transition to `EXPIRED`, `isActive=false`, no outbound
  message (FR-004c).
- Only one `isActive=true` session per `canonicalPhone` at a time (partial unique index).

## Entity: InboundMessage

Idempotency ledger for every inbound WhatsApp message (FR-013, message idempotency).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `messageId` | string | UNIQUE, NOT NULL | Provider `message_id` or derived key (research item 7) |
| `canonicalPhone` | string | NOT NULL | |
| `rawPayload` | JSONB | NOT NULL | Stored for audit/debugging, no unnecessary PII beyond message content |
| `normalizedText` | string | NOT NULL | |
| `processingStatus` | enum(`RECEIVED`,`PROCESSED`,`FAILED`) | NOT NULL | |
| `cachedResponse` | JSONB | NULL | `{handled, reply}` stored once computed, replayed on duplicate delivery |
| `sessionId` | UUID | FK → ConversationSession, NULL | Set once ownership resolved as `handled:true` |
| `createdAt` | datetime | NOT NULL | |

**Validation rules**: Insert is attempted first; unique-constraint violation on `messageId` short-circuits
processing and returns the stored `cachedResponse` unchanged (research item 4) — guarantees NFR-001.

## Entity: Booking

Deterministic booking record and lifecycle (FR-006–FR-012, State Model).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | Booking identifier |
| `bookingAttemptId` | UUID | UNIQUE, NOT NULL | Idempotency key sent to Hello Oscar (research item 5) |
| `customerId` | UUID | FK → Customer, NOT NULL | |
| `customerName` | string | NOT NULL | Denormalized for admin display per Data Requirements |
| `businessName` | string | NOT NULL | Denormalized for admin display |
| `meetingDate` | date | NOT NULL | |
| `meetingTime` | time | NOT NULL | |
| `location` | string | NOT NULL | |
| `status` | enum | NOT NULL | `PROPOSED \| CONFIRMATION_PENDING \| BOOKING_IN_PROGRESS \| CONFIRMED \| FAILED \| CANCELLED \| UNRESOLVED` |
| `externalBookingId` | string | NULL | Set only on `CONFIRMED`, from Hello Oscar (FR-010) |
| `sessionId` | UUID | FK → ConversationSession, NOT NULL | |
| `createdAt` | datetime | NOT NULL | |
| `updatedAt` | datetime | NOT NULL | |

**State transitions** (Business Rules service only; LangChain agent has no write path):

```text
PROPOSED --(explicit confirmation received)--> CONFIRMATION_PENDING
CONFIRMATION_PENDING --(confirmation summary accepted, all fields valid)--> BOOKING_IN_PROGRESS
BOOKING_IN_PROGRESS --(Hello Oscar success)--> CONFIRMED
BOOKING_IN_PROGRESS --(Hello Oscar rejection/timeout)--> FAILED
BOOKING_IN_PROGRESS --(no determinable result)--> UNRESOLVED
UNRESOLVED --(reconciliation resolves success)--> CONFIRMED
UNRESOLVED --(reconciliation resolves failure)--> FAILED
CONFIRMED --(approved cancellation actor)--> CANCELLED
PROPOSED/CONFIRMATION_PENDING --(silent expiry, no confirmation)--> (session EXPIRED; booking row not
  created until BOOKING_IN_PROGRESS, so pre-confirmation drafts that expire leave no Booking row —
  only the ConversationSession.context draft is discarded)
```

- A `Booking` row is only ever created when transitioning into `BOOKING_IN_PROGRESS` (i.e., after
  explicit confirmation). Earlier `PROPOSED`/`CONFIRMATION_PENDING` states are tracked purely in
  `ConversationSession.context` until confirmation, avoiding partial/abandoned Booking rows for every
  draft (keeps the Booking table equal to "real attempts," consistent with FR-011's "never confirmed
  based solely on a submitted request").
- Every transition is written inside a DB transaction with an append-only `BookingStateTransition` log
  (see below) to preserve auditability and support NFR-006 observability/traceability.

## Entity: BookingStateTransition (audit log)

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `bookingId` | UUID | FK → Booking, NOT NULL | |
| `fromStatus` | enum | NULL | Null for initial creation |
| `toStatus` | enum | NOT NULL | |
| `reason` | string | NULL | e.g. Hello Oscar error code, timeout, reconciliation source |
| `correlationId` | string | NOT NULL | conversation/session id + message_id, for NFR-006 |
| `createdAt` | datetime | NOT NULL | |

## Entity: AdminUser

Single administrator role authentication (Admin Authentication, NFR-003).

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `email` | string | UNIQUE, NOT NULL | |
| `passwordHash` | string | NOT NULL | bcrypt, never returned in any API response |
| `createdAt` | datetime | NOT NULL | |
| `lastLoginAt` | datetime | NULL | |

## Entity: CsvUploadBatch / CsvUploadRow (audit for CSV Requirements)

| Field (`CsvUploadBatch`) | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `uploadedByAdminId` | UUID | FK → AdminUser |
| `fileName` | string | |
| `totalRows` | int | |
| `acceptedRows` | int | |
| `rejectedRows` | int | |
| `createdAt` | datetime | |

| Field (`CsvUploadRow`) | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `batchId` | UUID | FK → CsvUploadBatch |
| `rowNumber` | int | 1-based, matches source file for error reporting (FR-018) |
| `outcome` | enum(`CREATED`,`UPDATED`,`SKIPPED`,`REJECTED`) | |
| `errorReason` | string | NULL unless `REJECTED` |
| `rawRowData` | JSONB | For audit; no secrets |

**Rationale**: Satisfies FR-018/FR-019 (row-level accepted/rejected/duplicate/processing-error outcomes)
and gives administrators a durable summary beyond the immediate HTTP response.

## Cross-cutting notes

- All monetary/secret fields: none exist in this data model; Hello Oscar credentials live only in
  backend configuration/secret storage, never in any table exposed via admin API.
- Retention/deletion (NFR-004, spec Open Question 2): schema above supports adding a `deletedAt`
  soft-delete column or a scheduled purge job per entity once the deletion policy is approved; not
  implemented until that policy is confirmed.
