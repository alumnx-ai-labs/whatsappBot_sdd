---

description: "Task list for feature implementation"
---

# Tasks: WhatsApp Meeting Assistant

**Input**: Design documents from `/specs/001-whatsapp-meeting-assistant/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The spec defines an explicit "Independent Test" per user story and the constitution
(Principles XI, XIX) requires testable, verifiable requirements with failure-path coverage, so contract,
unit, and integration test tasks are part of this breakdown.

**Organization**: Tasks are grouped by user story (from spec.md: US1–US4) to enable independent
implementation and testing of each story.

**Stack note**: This revision of the plan uses **Python 3.11+ / FastAPI / LangChain (Python) / SQLAlchemy
+ Alembic / SQLite** for the backend (superseding an earlier Node.js/TypeScript/Prisma/PostgreSQL
scaffold already present in `backend/`), and keeps the existing **React + TypeScript** frontend. No
browser e2e project is included. Phase 1 includes an explicit task to retire the obsolete TypeScript
backend scaffold before the Python one is built in its place.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- File paths are relative to the repository root per plan.md's `backend/` (Python) + `frontend/`
      (React/TS) layout.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Retire the superseded TypeScript backend scaffold and initialize the Python backend;
the frontend scaffold is verified separately and no e2e project is created.

- [X] T001 Confirm with repository owner and then remove the obsolete Node.js/TypeScript/Prisma backend
      scaffold (`backend/src/`, `backend/tests/`, `backend/prisma/`, `backend/package.json`,
      `backend/package-lock.json`, `backend/tsconfig.json`, `backend/vitest.config.ts`,
      `backend/.eslintrc.cjs`, `backend/node_modules/`) — this is a destructive, hard-to-reverse action
      and MUST be confirmed before deletion
- [X] T002 Create the Python backend project skeleton (`backend/app/__init__.py`, `backend/app/main.py`
      placeholder, `backend/pyproject.toml` or `backend/requirements.txt` +
      `backend/requirements-dev.txt`) targeting Python 3.11+
- [X] T003 [P] Add FastAPI + Uvicorn + Pydantic v2 + SQLAlchemy 2.x + Alembic + `langchain` +
      `langchain-openai` (or configured provider) + `passlib[bcrypt]` + `python-jose`/`itsdangerous` +
      `python-multipart` (CSV upload) to `backend/requirements.txt`
- [X] T004 [P] Add Pytest + `httpx` (for FastAPI `TestClient`) + `pytest-asyncio` + `ruff` + `black` to
      `backend/requirements-dev.txt`
- [X] T005 [P] Configure `ruff`/`black` in `backend/pyproject.toml`
- [X] T006 [P] Configure Pytest (`testpaths`, `asyncio_mode`) in `backend/pytest.ini` or
      `backend/pyproject.toml`
- [X] T007 Initialize Alembic in `backend/alembic.ini` and `backend/app/db/alembic/env.py`, pointed at a
      local SQLite file via `DATABASE_URL`
- [X] T008 Create backend `.env.example` documenting required config (SQLite file path, admin session
      signing secret, Hello Oscar base URL/credentials placeholders, LLM provider key) in
      `backend/.env.example` — no secrets committed
- [ ] T009 [P] Verify `frontend/` (React + Vite + TypeScript, already scaffolded) still matches
      plan.md's frontend structure; no changes needed unless drift is found
- [X] T010 [P] Confirm no browser e2e project is required or present; integration tests cover the
      end-to-end request path without adding an `e2e/` directory
- [X] T011 [P] Update root `.gitignore`/`.dockerignore` for Python patterns (`__pycache__/`, `*.pyc`,
      `.venv/`, `*.egg-info/`, local SQLite file e.g. `backend/data/*.db`) alongside existing Node.js
      patterns

**Checkpoint**: Python backend project installs (`pip install -r requirements.txt`) and boots an empty
FastAPI app; the existing frontend remains separate and no e2e project is required.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented,
including full admin authentication (shared by US3 and US4).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T012 Define all SQLAlchemy models (Customer, BusinessMetadata, ConversationSession,
      InboundMessage, Booking, BookingStateTransition, AdminUser, CsvUploadBatch, CsvUploadRow) per
      data-model.md in `backend/app/db/models.py`
- [X] T013 Create the SQLite engine/session factory (`backend/app/db/session.py`) and generate + apply
      the initial Alembic migration in `backend/app/db/alembic/versions/`
- [X] T014 [P] Implement structured (JSON) logging configuration with correlation-id support in
      `backend/app/shared/logging.py`
- [X] T015 [P] Implement centralized FastAPI exception handlers (no secrets/PII leakage) in
      `backend/app/shared/errors.py`
- [X] T016 [P] Implement Pydantic Settings-based config loader in `backend/app/shared/config.py`
- [X] T017 Implement canonical phone number normalizer (E.164, default country IN, via
      `phonenumbers`) in `backend/app/webhook/phone_normalizer.py`
- [X] T018 [P] Unit tests for phone normalizer (all three example formats normalize identically) in
      `backend/tests/unit/test_phone_normalizer.py`
- [X] T019 Implement FastAPI app factory and ASGI entrypoint in `backend/app/main.py`
- [X] T020 Implement AdminUser repository (bcrypt password hashing) in
      `backend/app/admin/auth/admin_user_repository.py`
- [X] T021 Implement admin session issuance/validation service (HttpOnly, Secure, SameSite=Strict
      cookie) in `backend/app/admin/auth/session_service.py`
- [X] T022 Implement `POST /admin/auth/login`, `POST /admin/auth/logout`, `GET /admin/auth/session` per
      contracts/admin-auth.md in `backend/app/admin/auth/router.py`
- [X] T023 Implement an admin-session-required FastAPI dependency protecting all `/admin/*` routes in
      `backend/app/admin/auth/require_session.py`
- [X] T024 [P] Contract tests for admin auth API (login success/failure, logout, session check,
      unauthenticated access to a protected route) using `TestClient` in
      `backend/tests/contract/test_admin_auth.py`
- [X] T025 Create a seed script creating a test `AdminUser` in `backend/app/seed.py`
      (`python -m app.seed`)
- [X] T026 Mount the auth router and exception handlers in `backend/app/main.py`
- [X] T027 Scaffold/verify React app shell: routing, layout, `AuthContext`/`useAuth`, `ProtectedRoute` in
      `frontend/src/app/App.tsx`, `frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/ProtectedRoute.tsx`
- [X] T028 [P] Implement/verify frontend API client base (fetch wrapper sending credentials, centralized
      error shape) in `frontend/src/services/api/client.ts` and `frontend/src/services/api/authApi.ts`
- [X] T029 Build/verify `LoginPage` (login form, calls `authApi`, redirects on success) in
      `frontend/src/pages/LoginPage.tsx`

**Checkpoint**: Foundation ready — SQLite schema, logging, config, phone normalization, and full admin
authentication work end-to-end against the FastAPI backend. User story implementation can now begin.

---

## Phase 3: User Story 1 - Visitor schedules a confirmed meeting (Priority: P1) 🎯 MVP

**Goal**: A visitor contacts via WhatsApp, is recognized or onboarded, provides meeting details, confirms
an appointment, and receives a booking outcome that is CONFIRMED only after Hello Oscar succeeds.

**Independent Test**: Using a test WhatsApp conversation and a controlled/stubbed Hello Oscar, verify a
returning and a new visitor can reach a confirmed booking, and provider failure never produces a
confirmation.

- [X] T030 [P] [US1] Contract test `POST /webhook-sync` for the approved normalized payload shape in
      `backend/tests/contract/test_webhook_sync.py`
- [X] T031 [P] [US1] Contract test `POST /webhook-sync` for the raw SkaleBot payload shape and field
      mapping in `backend/tests/contract/test_webhook_sync_skalebot.py`
- [X] T032 [US1] Implement payload normalizer (approved contract + raw SkaleBot →
      `NormalizedInboundMessage{phone, text, message_id}`) in `backend/app/webhook/payload_normalizer.py`
- [X] T033 [P] [US1] Unit tests for payload normalizer, including derived-key fallback when `message_id`
      is absent in `backend/tests/unit/test_payload_normalizer.py`
- [X] T034 [US1] Implement `InboundMessage` idempotency service (insert-first-if-absent, cached-response
      replay) in `backend/app/conversation/idempotency_service.py`
- [X] T035 [P] [US1] Unit tests for idempotency service (duplicate `message_id` returns identical cached
      response, no reprocessing) in `backend/tests/unit/test_idempotency_service.py`
- [X] T036 [US1] Implement message ownership detector (active-session rule; generic greetings without a
      session return not-owned) in `backend/app/webhook/ownership_detector.py`
- [X] T037 [P] [US1] Unit tests for ownership detector, including `hi`/`hello`/`hie` with no active
      session → `handled:false` in `backend/tests/unit/test_ownership_detector.py`
- [X] T038 [US1] Implement `Customer` repository (lookup/create by canonical phone) in
      `backend/app/db/customer_repository.py`
- [X] T039 [US1] Implement `ConversationSession` repository + service (create, load, resume,
      one-active-session-per-phone) in `backend/app/conversation/conversation_session_repository.py`
      and `backend/app/conversation/conversation_session_service.py`
- [X] T040 [P] [US1] Unit tests for conversation session service (returning vs. new visitor resolution,
      resume) in `backend/tests/unit/test_conversation_session_service.py`
- [X] T041 [US1] Define LangChain agent structured-output Pydantic schema (`intent`, `extracted_fields`,
      `missing_fields`, `proposed_reply_draft`, `requested_action`) in
      `backend/app/agent/output_schemas.py`
- [X] T042 [US1] Implement LangChain agent runner (per-turn invocation with session context, using
      LangChain's structured-output / tool-calling) in `backend/app/agent/langchain_agent.py`
- [X] T043 [P] [US1] Implement agent structured tools for onboarding/meeting-info collection (read-only,
      no transactional side effects) in `backend/app/agent/tools/`
- [ ] T044 [P] [US1] Unit tests validating the agent never returns a booking-confirmation action and
      always conforms to the output schema in `backend/tests/unit/test_agent_output_schema.py`
- [X] T045 [US1] Implement deterministic booking state machine (`PROPOSED → CONFIRMATION_PENDING →
      BOOKING_IN_PROGRESS → CONFIRMED/FAILED/UNRESOLVED`) with transition logging in
      `backend/app/business_rules/booking_state_machine.py`
- [X] T046 [P] [US1] Unit tests for booking state machine valid/invalid transitions in
      `backend/tests/unit/test_booking_state_machine.py`
- [X] T047 [US1] Implement confirmation rules (explicit confirmation required before booking; ambiguous
      input rejected) in `backend/app/business_rules/confirmation_rules.py`
- [X] T048 [P] [US1] Unit tests for confirmation rules in
      `backend/tests/unit/test_confirmation_rules.py`
- [X] T049 [US1] Implement Hello Oscar adapter interface and a stub/mock implementation per
      contracts/hello-oscar-integration.md (timeout → `unresolved`, never fabricated `confirmed`) in
      `backend/app/integrations/hello_oscar/hello_oscar_client.py` and
      `backend/app/integrations/hello_oscar/hello_oscar_types.py`
- [X] T050 [P] [US1] Unit tests for Hello Oscar adapter timeout/error/success mapping in
      `backend/tests/unit/test_hello_oscar_client.py`
- [X] T051 [US1] Implement `Booking` repository + `BookingService` (create attempt with idempotency key,
      invoke Hello Oscar, persist result + state transitions) in
      `backend/app/booking/booking_repository.py` and `backend/app/booking/booking_service.py`
- [X] T052 [US1] Implement the webhook route handler wiring the full pipeline (validate → normalize →
      phone-normalize → idempotency → ownership → session → agent → business rules → booking → reply)
      in `backend/app/webhook/webhook_router.py`
- [X] T053 [US1] Mount `POST /webhook-sync` router in `backend/app/main.py`
- [ ] T054 [P] [US1] Integration test: returning visitor confirms and Hello Oscar succeeds → `CONFIRMED`
      with external booking id stored in `backend/tests/integration/test_booking_confirmed_flow.py`
- [ ] T055 [P] [US1] Integration test: new visitor onboarding + valid meeting request reaches a proposal
      in `backend/tests/integration/test_new_visitor_onboarding.py`
- [ ] T056 [P] [US1] Integration test: Hello Oscar failure/timeout/ambiguous result never yields
      `CONFIRMED` and records a recoverable outcome in
      `backend/tests/integration/test_booking_failure_flow.py`
- [ ] T057 [P] [US1] Integration test: duplicate `message_id` delivery produces no duplicate
      session/booking/transition rows in
      `backend/tests/integration/test_duplicate_message_idempotency.py`
- [X] T058 [P] [US1] Integration test covering quickstart Scenarios 1–6 (unrelated greeting, SkaleBot
      normalization, onboarding, confirmation, Hello Oscar failure, duplicate delivery) in
      `backend/tests/integration/test_whatsapp_booking_flow.py`

**Checkpoint**: User Story 1 is independently functional and testable — this is the MVP.

---

## Phase 4: User Story 2 - Visitor corrects or abandons a proposal (Priority: P1)

**Goal**: A visitor can modify appointment details before booking or stop responding without an
unintended booking.

**Independent Test**: Present a proposed appointment, submit a modification, cancellation, ambiguous
reply, and no reply; verify each path leaves the booking unconfirmed until later explicit confirmation.

- [ ] T059 [US2] Extend confirmation rules to accept date/time/location modification while
      `CONFIRMATION_PENDING`, re-presenting the revised proposal without booking in
      `backend/app/business_rules/confirmation_rules.py`
- [ ] T060 [P] [US2] Unit tests for proposal modification (updates proposal, does not transition to
      `BOOKING_IN_PROGRESS`) in `backend/tests/unit/test_confirmation_rules_modification.py`
- [X] T061 [US2] Implement silent proposal expiry service (configurable `PROPOSAL_EXPIRY_MINUTES`, lazy
      check-on-read, no outbound message) in `backend/app/business_rules/expiry_service.py`
- [ ] T062 [P] [US2] Unit tests for expiry service (no reminder sent, session marked
      `EXPIRED`/inactive, cannot be booked afterward) in `backend/tests/unit/test_expiry_service.py`
- [X] T063 [US2] Integrate expiry check into `conversation_session_service.py`'s session-load path
- [ ] T064 [P] [US2] Integration test: ambiguous reply during `CONFIRMATION_PENDING` keeps proposal
      unbooked and reprompts in `backend/tests/integration/test_ambiguous_reply_flow.py`
- [ ] T065 [P] [US2] Integration test: visitor stops responding until expiry elapses — proposal silently
      expires, no booking, new interaction required in
      `backend/tests/integration/test_proposal_expiry_flow.py`
- [ ] T066 [P] [US2] Integration test: propose → modify → confirm succeeds; propose → abandon → expires
      safely in `backend/tests/integration/test_proposal_correction_flow.py`

**Checkpoint**: User Stories 1 and 2 together deliver the complete, safe WhatsApp booking journey.

---

## Phase 5: User Story 3 - Administrator manages business and customer metadata (Priority: P2)

**Goal**: An authorized administrator can add/update metadata via a single-entry form and bulk CSV
upload, with validation and deterministic duplicate handling.

**Independent Test**: As an authorized administrator, submit valid and invalid single records and a CSV
containing valid, invalid, duplicate, and existing records; verify the documented outcomes and error
report.

- [ ] T067 [US3] Implement `BusinessMetadata` repository (create/update/find-by-phone) in
      `backend/app/admin/metadata/metadata_repository.py`
- [X] T068 [US3] Implement metadata request validation schema (Pydantic) in
      `backend/app/admin/metadata/metadata_schema.py`
- [X] T069 [US3] Implement metadata service applying the deterministic duplicate policy
      (create/update/report outcome) in `backend/app/admin/metadata/metadata_service.py`
- [X] T070 [US3] Implement `POST /admin/metadata`, `PUT /admin/metadata/{id}`,
      `GET /admin/metadata[/{id}]` per contracts/admin-metadata.md in
      `backend/app/admin/metadata/router.py`
- [ ] T071 [P] [US3] Contract tests for admin metadata API (create, update, validation failure with
      field errors) in `backend/tests/contract/test_admin_metadata.py`
- [X] T072 [US3] Implement CSV header/row parser and per-row validation (Python `csv` module) in
      `backend/app/admin/csv/csv_parser.py`
- [ ] T073 [US3] Implement `CsvUploadBatch`/`CsvUploadRow` repository in
      `backend/app/admin/csv/csv_upload_repository.py`
- [X] T074 [US3] Implement CSV upload service (partial success, per-row created/updated/skipped/rejected
      reporting, size/row limits) in `backend/app/admin/csv/csv_upload_service.py`
- [X] T075 [US3] Implement `POST /admin/metadata/csv` (FastAPI `UploadFile`) per contracts/admin-csv.md
      in `backend/app/admin/csv/router.py`
- [ ] T076 [P] [US3] Contract tests for CSV upload (valid rows, invalid rows, duplicate-within-file,
      malformed file, oversized file, missing headers) in `backend/tests/contract/test_admin_csv.py`
- [ ] T077 [P] [US3] Integration test: CSV with mixed valid/invalid/duplicate/existing rows reports every
      row with no silent loss in `backend/tests/integration/test_csv_mixed_rows.py`
- [X] T078 [US3] Mount admin metadata and CSV routers in `backend/app/main.py`
- [ ] T079 [US3] Build/verify `MetadataForm` component with client-side validation mirroring server
      rules in `frontend/src/components/metadata/MetadataForm.tsx`
- [ ] T080 [US3] Build/verify `MetadataPage` and `metadataApi` wiring the form to the backend in
      `frontend/src/pages/MetadataPage.tsx` and `frontend/src/services/api/metadataApi.ts`
- [ ] T081 [P] [US3] Frontend tests: metadata form validation errors and successful submission in
      `frontend/tests/integration/metadata-form.test.tsx`
- [ ] T082 [US3] Build/verify `CsvUploadForm` with file-upload progress indicator in
      `frontend/src/components/csv/CsvUploadForm.tsx` and
      `frontend/src/components/csv/ProgressIndicator.tsx`
- [ ] T083 [US3] Build/verify `ResultSummary` component rendering per-row outcomes
      (created/updated/skipped/rejected with reasons) in
      `frontend/src/components/csv/ResultSummary.tsx`
- [ ] T084 [US3] Build/verify `CsvUploadPage` and `csvApi` wiring upload + result display in
      `frontend/src/pages/CsvUploadPage.tsx` and `frontend/src/services/api/csvApi.ts`
- [ ] T085 [P] [US3] Frontend tests: CSV upload success, validation failures, partial-result rendering in
      `frontend/tests/integration/csv-upload.test.tsx`
- [ ] T086 [P] [US3] Frontend tests: unauthenticated access to metadata/CSV pages redirects to login in
      `frontend/tests/integration/admin-authorization.test.tsx`
- [ ] T087 [P] [US3] Integration test: admin auth, metadata submission, and mixed-result CSV upload
      (quickstart Scenarios 8–9) in `backend/tests/integration/test_admin_metadata_csv.py`

**Checkpoint**: Administrators can fully manage business/customer metadata independent of US4.

---

## Phase 6: User Story 4 - Administrator monitors confirmed bookings (Priority: P2)

**Goal**: An authorized administrator can view confirmed bookings with required fields and refresh the
list to observe newly confirmed meetings.

**Independent Test**: Seed confirmed, failed, pending, and cancelled outcomes; open the booking view and
verify only the confirmed set is shown with required fields; refresh after a new confirmation and verify
it appears.

- [ ] T088 [US4] Implement admin bookings query service filtering strictly on `status = CONFIRMED`
      server-side in `backend/app/admin/bookings/bookings_service.py`
- [X] T089 [US4] Implement `GET /admin/bookings` and `GET /admin/bookings/{id}` per
      contracts/admin-bookings.md in `backend/app/admin/bookings/router.py`
- [ ] T090 [P] [US4] Contract tests for admin bookings API (confirmed-only filter excludes
      failed/pending/cancelled, empty list, error state) in
      `backend/tests/contract/test_admin_bookings.py`
- [X] T091 [US4] Mount admin bookings router in `backend/app/main.py`
- [ ] T092 [US4] Build/verify `BookingList`/`BookingRow` components with loading, empty, and error states
      in `frontend/src/components/bookings/BookingList.tsx` and
      `frontend/src/components/bookings/BookingRow.tsx`
- [ ] T093 [US4] Build/verify `BookingsPage` and `bookingsApi` with a manual refresh action (preserves
      prior list during refresh) in `frontend/src/pages/BookingsPage.tsx` and
      `frontend/src/services/api/bookingsApi.ts`
- [ ] T094 [P] [US4] Frontend tests: booking list display, refresh behavior, empty state, API error state
      in `frontend/tests/integration/bookings-page.test.tsx`
- [ ] T095 [P] [US4] Integration test: admin retrieves confirmed bookings and refreshes to see a newly
      confirmed booking (quickstart Scenario 7) in `backend/tests/integration/test_admin_bookings.py`

**Checkpoint**: All four user stories are independently functional and integrated.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, documentation, and quality gates that span all user stories.

- [ ] T096 [P] Add structured, non-sensitive audit logging across webhook → agent → booking → Hello
      Oscar → reply using the shared correlation id in `backend/app/shared/logging.py` call sites
- [ ] T097 [P] Add request-rate/lockout protection to admin login in
      `backend/app/admin/auth/router.py`
- [ ] T098 [P] Verify no secrets or unnecessary PII appear in logs, error responses, or frontend bundles
      (manual review + `backend/tests/unit/test_log_redaction.py`)
- [ ] T099 [P] Add `BookingStateTransition` audit query support for manual reconciliation of
      `UNRESOLVED` bookings in `backend/app/booking/booking_repository.py`
- [ ] T100 [P] Document deployment/runbook basics (env vars, migration command, seed command) in
      `backend/README.md` and `frontend/README.md`
- [ ] T101 Run the full quickstart.md validation scenario suite (1–9) against a freshly seeded SQLite
      database and record results
- [ ] T102 [P] Performance check: confirm 95% of local (non-Hello-Oscar) webhook responses complete
      within 5s under representative load (NFR-007)
- [ ] T103 [P] Security review pass: confirm frontend has zero WhatsApp/LangChain/Hello Oscar imports or
      credentials (grep-based check) per the architecture boundary
- [ ] T104 Update `research.md`'s "Summary of open NEEDS CLARIFICATION items" with resolution status
      after this implementation pass
- [ ] T105 Final constitution compliance pass against all 20 principles in
      `.specify/memory/constitution.md`, recording any exceptions

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)**: strictly sequential; Phase 2 blocks all user stories.
  T001 (removing the obsolete TypeScript scaffold) must be confirmed with the repository owner and
  completed before T002 (Python skeleton) to avoid the two backends coexisting.
- **Phase 3 (US1, P1)**: depends only on Phase 2. This is the MVP.
- **Phase 4 (US2, P1)**: depends on Phase 3 (extends the same conversation/booking flow and files:
  `confirmation_rules.py`, `conversation_session_service.py`). Not parallelizable with Phase 3.
- **Phase 5 (US3, P2)**: depends only on Phase 2 (admin auth) — independent of Phases 3 and 4, can be
  built in parallel by a different engineer/session once Phase 2 is done.
- **Phase 6 (US4, P2)**: depends on Phase 2 (admin auth) and on `Booking`/`BookingStateTransition`
  existing (from Phase 3) to have real data to query, but its own code is independent of US2/US3 files —
  can be built in parallel with Phase 5.
- **Phase 7 (Polish)**: depends on all preceding phases being complete.

Suggested MVP scope: **Phase 1 + Phase 2 + Phase 3 (US1)** — delivers a working, safe, Hello-Oscar-gated
WhatsApp booking flow with no admin dashboard yet.

## Parallel Execution Examples

Within Phase 2 (after T012/T013 schema/migration land): T014, T015, T016 can run in parallel (different
files); T018, T024 (test-writing) can run in parallel with each other once their targets exist.

Within Phase 3 (US1): T030/T031 (contract tests) in parallel; T033, T035, T037, T040, T044, T046, T048,
T050 (unit tests for already-designed modules) in parallel with each other; T054–T058 (integration tests)
in parallel once T052/T053 (webhook route wiring) is complete.

Across phases: once Phase 2 is complete, Phase 3 (US1/US2 track) and Phase 5 (US3 track) can be worked by
separate engineers in parallel; Phase 6 (US4) can start its own router/frontend work in parallel with
Phase 5, syncing only on shared `bookings` data becoming available from Phase 3.

## Implementation Strategy

1. Confirm and execute the TypeScript-scaffold removal (T001), then complete the rest of Phase 1 and all
   of Phase 2 — nothing else can start safely before this.
2. Deliver Phase 3 (US1) as the MVP: a visitor can complete a full WhatsApp booking journey with a
   truthful, Hello-Oscar-gated confirmation, now running on FastAPI + LangChain (Python) + SQLite.
3. Layer in Phase 4 (US2) immediately after — it extends the same conversation flow with correction/
   expiry safety and is also P1.
4. Deliver Phase 5 (US3) and Phase 6 (US4) — independent of each other and of the WhatsApp flow's
   internals beyond reading `Booking` data — to complete the admin dashboard (reusing the existing React
   frontend scaffold).
5. Finish with Phase 7 to harden security, performance, observability, and constitutional compliance
   before release.

## Phase 8: Convergence

**Purpose**: Close gaps found by assessing the current implementation against spec.md, plan.md, and
the existing task ledger. These tasks are appended without rewriting prior task history.

- [X] T106 Complete the P1 WhatsApp scheduling path by implementing the LangChain runner, deterministic
      confirmation/business rules, Hello Oscar adapter, BookingService, and wiring the full pipeline into
      `backend/app/webhook/webhook_router.py` per FR-004–FR-012 and US1/AC1–AC5 (missing, CRITICAL)
- [X] T107 Make `backend/app/conversation/idempotency_service.py` safe for concurrent duplicate webhook
      deliveries by handling SQLite unique-key races transactionally and preserving one cached response
      per `message_id` per NFR-001 and FR-013 (partial, HIGH)
- [X] T108 Implement the protected metadata, CSV, and confirmed-bookings admin API routers and services
      in `backend/app/admin/metadata/`, `backend/app/admin/csv/`, and `backend/app/admin/bookings/`, then
      implement the React admin dashboard pages/components in `frontend/src/` per FR-015–FR-022 (missing,
      HIGH)
- [X] T109 Integrate silent proposal expiry into the session load path and reject confirmations after
      expiry in `backend/app/conversation/conversation_session_service.py` and
      `backend/app/business_rules/expiry_service.py` per FR-004c and US2/AC3 (partial, HIGH)
- [X] T110 Reject the development fallback admin session secret when `environment` is not development,
      and add a configuration test in `backend/app/shared/config.py` and
      `backend/tests/unit/test_config.py` per NFR-003 and Constitution IX (partial, MEDIUM)
- [ ] T111 Reconcile stale e2e/Playwright references in the existing task-document descriptions with the
      descoped no-e2e decision, without modifying earlier task IDs or implementation artifacts, in
      `specs/001-whatsapp-meeting-assistant/tasks.md` per plan: testing decision (partial, MEDIUM)

## Phase 9: Convergence

**Purpose**: Close remaining gaps found by the latest assessment of the current implementation against
spec.md, plan.md, and this task ledger. This section is append-only.

- [ ] T112 Implement the React administrative dashboard, including login/session route protection,
      confirmed-bookings display/refresh/loading/empty/error states, metadata form, CSV upload and result
      reporting, with frontend tests in `frontend/src/` and `frontend/tests/` per FR-015–FR-022 (missing,
      HIGH)
- [X] T113 Implement silent proposal expiry for stale `PROPOSED` and `CONFIRMATION_PENDING` sessions,
      integrate it into session loading, reject post-expiry confirmations, and add tests in
      `backend/app/business_rules/expiry_service.py`,
      `backend/app/conversation/conversation_session_service.py`, and
      `backend/tests/unit/test_expiry_service.py` per FR-004c and US2/AC3 (missing, HIGH)
- [X] T114 Make `backend/app/conversation/idempotency_service.py` handle concurrent SQLite unique-key
      races transactionally and add a duplicate-delivery concurrency test in
      `backend/tests/integration/test_duplicate_message_idempotency.py` per NFR-001 and FR-013
      (partial, HIGH)
- [ ] T115 Complete the injectable LangChain model/provider construction and read-only onboarding and
      meeting-information tools, then add a TestClient integration suite for new/returning visitors,
      natural-language extraction, explicit confirmation, provider success/failure, and duplicate
      delivery in `backend/app/agent/`, `backend/app/webhook/`, and
      `backend/tests/integration/` per FR-004–FR-012 and US1/AC1–AC5 (partial, HIGH)
- [X] T116 Correct `PUT /admin/metadata/{id}` so it updates only the path-selected record and rejects a
      submitted phone number already owned by another record; add regression coverage in
      `backend/app/admin/metadata/router.py`, `backend/app/admin/metadata/metadata_service.py`, and
      `backend/tests/contract/test_admin_metadata.py` per FR-015–FR-016 and US3/AC1 (contradicts, HIGH)
- [ ] T117 Add correlation-id structured logs at webhook receipt, ownership result, agent invocation,
      session transition, booking attempt, Hello Oscar result, and final reply, with redaction tests in
      `backend/app/shared/logging.py`, `backend/app/webhook/`, `backend/app/booking/`, and
      `backend/tests/unit/test_log_redaction.py` per FR-023 and NFR-006 (missing, MEDIUM)
- [ ] T118 Add FastAPI integration tests for booking failure/timeout, CSV mixed-row partial success,
      confirmed-only admin bookings, proposal correction, and silent expiry in
      `backend/tests/integration/` per FR-012, FR-018–FR-021, US2–US4 (missing, MEDIUM)
- [ ] T119 Add server-side admin session revocation on logout or document and test the accepted
      short-lived-token security model so a copied pre-logout token cannot remain usable unexpectedly in
      `backend/app/admin/auth/session_service.py`, `backend/app/admin/auth/router.py`, and
      `backend/tests/contract/test_admin_auth.py` per NFR-003 and Constitution IX (partial, MEDIUM)

## Phase 10: Convergence

**Purpose**: Close gaps found by the latest implementation assessment. This section is append-only.

- [X] T120 Define and implement the approved first-contact ownership trigger for the shared WhatsApp
      number, then cover a genuinely new visitor entering onboarding through `backend/app/webhook/`
      and `backend/tests/contract/` per FR-002–FR-003 and US1/AC3 (missing, HIGH)
- [X] T121 Add deterministic validation for past/invalid meeting dates, invalid times, and unsupported
      locations before proposal or booking state advances in `backend/app/business_rules/`, with tests
      in `backend/tests/unit/` per FR-004–FR-005 and US1/AC2 (missing, HIGH)
- [X] T122 Catch Hello Oscar transport exceptions and timeout failures in
      `backend/app/booking/booking_service.py`, persist `FAILED` or `UNRESOLVED` rather than leaving a
      `BOOKING_IN_PROGRESS` record, and add recovery-path integration tests per FR-009–FR-012 and the
      Hello Oscar failure edge cases (partial, HIGH)
- [X] T123 Prevent a second booking attempt for a session/customer while an existing booking is
      `BOOKING_IN_PROGRESS`, `CONFIRMED`, or `UNRESOLVED`, including distinct confirmation message IDs,
      in `backend/app/booking/booking_service.py` with regression tests per FR-013 and Business Rule 5
      (partial, HIGH)
- [ ] T124 Add frontend component and integration tests for login protection, bookings loading/empty/
      error/refresh states, metadata validation/submission, and CSV result rendering in
      `frontend/tests/` per FR-015–FR-022 and the frontend testing strategy (missing, MEDIUM)
- [ ] T125 Emit structured correlation-id logs at webhook receipt, ownership, agent, session, booking,
      provider result, and reply stages, and verify redaction in
      `backend/app/shared/logging.py` and `backend/tests/` per FR-023, NFR-006, and Constitution XV
      (missing, MEDIUM)
- [X] T126 Implement admin session revocation on logout, or explicitly document and test the selected
      short-lived-token behavior, in `backend/app/admin/auth/session_service.py` and
      `backend/tests/contract/test_admin_auth.py` per NFR-003 and Constitution IX (missing, MEDIUM)

## Phase 11: Convergence

**Purpose**: Record remaining gaps found by the latest assessment of the implemented code against the
specification, plan, task ledger, and constitution. This section is append-only.

- [ ] T127 Configure the Gemini runtime key for the LangChain `create_agent(model="google_genai:gemini-3.6-flash", ...)` path so the configured backend setting is passed to the provider without exposing it to the frontend, and add a construction test in `backend/app/agent/langchain_agent.py`, `backend/app/shared/config.py`, and `backend/tests/unit/` per plan: LangChain provider decision and Constitution IX (partial, HIGH)
- [ ] T128 Obtain and implement the approved Hello Oscar HTTP transport contract, including authentication, endpoint/schema validation, timeout/retry policy, and reconciliation behavior, in `backend/app/integrations/hello_oscar/` per FR-008–FR-012, FR-025, and Constitution IV (missing, HIGH)
- [ ] T129 Handle inbound non-text WhatsApp payloads such as voice/image/media by returning a clear text-only response and persisting the result without invoking LangChain or booking logic in `backend/app/webhook/` with contract tests per FR-001a (missing, HIGH)
- [ ] T130 Document and test the exact shared-number ownership trigger (`Hello Oscar`) in the webhook contract and ownership tests, ensuring generic greetings without an active session remain `handled:false`, in `specs/001-whatsapp-meeting-assistant/contracts/webhook-sync.md` and `backend/tests/contract/` per FR-001–FR-003 (partial, MEDIUM)
- [ ] T131 Add frontend component/integration tests for login protection, bookings loading/empty/error/refresh states, metadata validation/submission, and CSV result rendering in `frontend/tests/` per FR-015–FR-022 and the plan testing strategy (missing, MEDIUM)
- [ ] T132 Add FastAPI integration tests for proposal correction, silent expiry, duplicate confirmation delivery, CSV mixed-row processing, confirmed-only booking reads, and provider exception recovery in `backend/tests/integration/` per FR-012–FR-021 and US2–US4 (missing, MEDIUM)
- [ ] T133 Add deployment/runbook documentation for starting the FastAPI backend, applying the SQLite migration, seeding an administrator, configuring `GOOGLE_API_KEY`, and running the React dashboard in `backend/README.md` and `frontend/README.md` per plan: quickstart and Constitution XIX (missing, LOW)

## Phase 12: Convergence

**Purpose**: Record remaining gaps found by the latest implementation assessment. This section is
append-only and does not replace earlier convergence tasks.

- [ ] T134 Ensure the configured `GOOGLE_API_KEY` is made available to the Google GenAI provider used by
      `create_agent(model="google_genai:gemini-3.6-flash", ...)`, without logging or exposing the secret,
      and add a provider-construction test in `backend/app/agent/langchain_agent.py` and
      `backend/tests/unit/` per the LangChain provider decision and Constitution IX (partial, HIGH)
- [ ] T135 Obtain and implement the approved Hello Oscar HTTP contract, including authentication,
      endpoint/request/response schemas, timeout/retry behavior, external booking ID handling, and
      reconciliation of uncertain outcomes in `backend/app/integrations/hello_oscar/` per FR-008–FR-012,
      FR-025, and Constitution IV (missing, HIGH)
- [ ] T136 Handle voice, image, and other non-text WhatsApp payloads with a clear text-only response,
      persisted idempotency state, and no agent or booking invocation in `backend/app/webhook/`, with
      contract coverage in `backend/tests/contract/` per FR-001a (missing, HIGH)
- [ ] T137 Implement proposal modification and ambiguous-response handling so date, time, and location
      changes revise the pending proposal without booking, in `backend/app/business_rules/`,
      `backend/app/agent/`, and `backend/app/webhook/`, with integration coverage per FR-007 and US2
      (missing, HIGH)
- [ ] T138 Prevent provider calls when meeting availability is unknown or a requested slot is unavailable,
      and define the deterministic availability/recovery behavior in `backend/app/business_rules/` and
      `backend/app/booking/` per FR-004, FR-005, FR-012, and the availability edge cases (missing, HIGH)
- [ ] T139 Add frontend component and integration test coverage for login authorization, confirmed-booking
      loading/empty/error/refresh states, metadata validation/submission, and CSV row-result rendering in
      `frontend/tests/` per FR-015–FR-022 and the plan testing strategy (missing, MEDIUM)
- [ ] T140 Add backend integration coverage for CSV partial success, confirmed-only bookings, proposal
      correction/expiry, duplicate confirmations, provider timeout/exception recovery, and raw/non-text
      webhook handling in `backend/tests/integration/` per FR-001a, FR-012–FR-021, and US1–US4 (missing,
      MEDIUM)
- [ ] T141 Define and implement webhook authenticity/provenance validation and delivery-failure handling
      before accepting inbound traffic in `backend/app/webhook/`, with contract tests per the Security
      and Privacy Requirements and WhatsApp integration contract (missing, MEDIUM)
- [ ] T142 Add database-backed correlation/audit event persistence or an equivalent verifiable trace across
      conversation, booking attempt, provider request/result, state transition, and user-visible reply in
      `backend/app/shared/`, `backend/app/conversation/`, and `backend/app/booking/` per FR-023 and NFR-006
      (partial, MEDIUM)
