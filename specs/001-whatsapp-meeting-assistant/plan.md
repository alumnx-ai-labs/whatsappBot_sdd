# Implementation Plan: WhatsApp Meeting Assistant

**Branch**: `001-whatsapp-meeting-assistant` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-whatsapp-meeting-assistant/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Deliver a two-application system: (1) a Python backend service that owns all WhatsApp conversation
handling, a LangChain agent for natural-language interpretation, deterministic booking business rules,
Hello Oscar integration, and administrative APIs; and (2) a React administrative dashboard that
consumes only the backend admin APIs to display confirmed bookings and manage business/customer
metadata. The frontend never talks to WhatsApp, the LangChain agent, or Hello Oscar directly — it is a
pure data-management client over authenticated backend APIs. The backend enforces a strict boundary
between AI interpretation (LangChain) and transactional truth (deterministic business/booking services),
matches the shared-number ownership rule (`handled:false` unless the message provably belongs to this
bot), and normalizes both the approved webhook contract and the raw SkaleBot payload shape before
processing.

## Technical Context

**Language/Version**: Python 3.11+ (backend), React 18 + TypeScript 5 (frontend). Python is used for the
backend specifically because `langchain` (Python) is the reference LangChain implementation with the
broadest tool/agent ecosystem; the frontend stays TypeScript since it is a separate, independently
running application with no shared code/runtime with the backend.

**Primary Dependencies**:
- Backend: FastAPI (HTTP/webhook + admin API framework) with Uvicorn ASGI server, `langchain` +
  `langchain-openai` (or configured provider) for the agent and structured-output tool-calling, Pydantic
  v2 for request/payload/schema validation (native to FastAPI), SQLAlchemy 2.x ORM + Alembic for
  migrations, Python's built-in `csv` module for CSV ingestion, `passlib[bcrypt]` for password hashing,
  `itsdangerous` or `PyJWT` for signed session/JWT cookies, Python `logging` configured for structured
  (JSON) output.
- Frontend: React + Vite, React Router, TanStack Query (data fetching/caching/refresh), a lightweight
  form library (React Hook Form + Zod resolver) for metadata forms and CSV upload UX.

**Storage**: SQLite as a single local file database (per this request — simple local storage, no
separate DB server to run). SQLAlchemy + Alembic still provide schema/migration structure so the same
models could later point at PostgreSQL with minimal change if scale requires it. SQLite's native
`UNIQUE` constraints are sufficient for the idempotency/duplicate-detection guarantees this feature
needs at MVP scale.

**Testing**: Backend — Pytest for unit + integration tests, FastAPI's `TestClient` (httpx-based) for
HTTP/webhook contract tests. Frontend — Vitest + React Testing Library for component/integration tests.
No end-to-end/browser-automation test suite is planned for this MVP (explicitly descoped); integration
tests against the FastAPI `TestClient` and a stubbed Hello Oscar integration cover the full
webhook-to-booking flow instead.

**Target Platform**: Linux server (containerized backend via Docker running Uvicorn/Gunicorn), static-
hosted React SPA (served by a CDN/static host or the backend as a fallback), both behind HTTPS.

**Project Type**: Web application (frontend + backend), per Option 2 structure below. Backend stack is
Python/FastAPI; frontend stack is React/TypeScript.

**Performance Goals**: 95% of local (non-Hello-Oscar) user-facing WhatsApp responses issued within 5s
(NFR-007); admin dashboard list/detail views load and refresh within normal interactive expectations
(SC-006: locate + refresh a booking in under 30s including human review time).

**Constraints**: No booking may be shown as CONFIRMED without an authoritative Hello Oscar success
result (NFR-002); no duplicate bookings/records from repeated `message_id`s or webhook retries
(NFR-001); credentials and secrets never reach the React client or logs (NFR-003); the frontend must
have zero WhatsApp/LangChain/Hello Oscar logic (architecture boundary, this request).

**Scale/Scope**: Single-tenant MVP, one administrator role, one shared WhatsApp number serviced
alongside other bots (ownership detection required), scoped to the four user stories and API groups
defined in this request and the approved spec.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Design response | Status |
|---|---|---|
| I. Requirements Before Implementation | Plan derives directly from approved spec.md; Hello Oscar contract fields remain explicit `NEEDS CLARIFICATION` rather than invented (see Research). | PASS |
| II. No False Booking Confirmation | Booking Service only transitions to `CONFIRMED` after a successful, schema-validated Hello Oscar response; LangChain agent cannot write booking state. | PASS |
| III. Explicit State Management | Booking state machine (`PROPOSED → CONFIRMATION_PENDING → BOOKING_IN_PROGRESS → CONFIRMED/FAILED/CANCELLED/UNRESOLVED`) implemented as a deterministic service, not agent output. | PASS |
| IV. External API Contract First | Hello Oscar integration is isolated behind an adapter interface; concrete endpoint/schema fields are marked `NEEDS CLARIFICATION` until the contract is supplied and approved — implementation of the adapter's internals is blocked on that approval, but the surrounding system (interface, retry/timeout policy shape, idempotency key, reconciliation state) is planned now. | PASS (conditionally blocked sub-part flagged) |
| V. Human-Readable Conversations | LangChain agent responsible only for generating reply text from structured, deterministic state; reviewed via WhatsApp response contract tests. | PASS |
| VI. User Confirmation Before Booking | `CONFIRMATION_PENDING` state requires an explicit affirmative match before any booking call is made; ambiguous replies stay in the same state. | PASS |
| VII. Fail Safely | `FAILED`/`UNRESOLVED` states preserve non-confirmed status and expose a recovery prompt; no partial writes without a transition record. | PASS |
| VIII. Idempotency and Duplicate Protection | `message_id` uniqueness constraint + inbound-message ledger; booking attempts keyed by conversation/session idempotency key before calling Hello Oscar. | PASS |
| IX. Security by Default | Admin auth required for all admin APIs; secrets (Hello Oscar keys, session/JWT signing key) stored only in backend env/secret store; the local SQLite file is kept outside the web-served directory and outside version control; frontend never receives them. | PASS |
| X. Minimal MVP Scope | Only the four API groups (auth, bookings, metadata, CSV) and the single webhook endpoint are planned; no chat UI, no extra admin roles. | PASS |
| XI. Testable Requirements | Test strategy section enumerates unit/integration coverage per functional requirement group (no e2e suite planned; see Technical Context). | PASS |
| XII. End-to-End Traceability | data-model.md and contracts trace back to FR IDs; tasks phase (later command) will map tasks to these. | PASS |
| XIII. Single Source of Truth | This plan defers to spec.md for behavior; no conflicting behavior introduced. | PASS |
| XIV. Controlled Requirement Changes | No requirement changes made in this plan; only technical realization decisions, captured in research.md. | PASS |
| XV. Observable Operations | Structured logging with correlation ID (conversation/session id + message_id) across webhook → agent → booking → Hello Oscar → reply. | PASS |
| XVI. Separation of Responsibilities | Layered backend: FastAPI Webhook Router → Normalization → Ownership → Conversation Service → LangChain Agent → Business Rules → Booking Service → Hello Oscar Adapter → Persistence (SQLAlchemy); Admin API router layer is fully independent. | PASS |
| XVII. AI Cannot Override Business Rules | LangChain agent emits structured tool-call output only; Business Rule Engine validates/authorizes every transactional effect. | PASS |
| XVIII. Data Minimization | Data model only stores fields listed in spec's Data Requirements; no extra PII fields planned. | PASS |
| XIX. Definition of Done | Test strategy requires failure-path and security coverage, not just happy path. | PASS |
| XX. Reliable Booking Visibility | Admin "confirmed bookings" API filters strictly on `status = CONFIRMED`; other states are excluded by query, not client-side filtering. | PASS |

No unjustified violations. Complexity Tracking table is empty (see below).

## Project Structure

### Documentation (this feature)

```text
specs/001-whatsapp-meeting-assistant/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── webhook-sync.md
│   ├── admin-auth.md
│   ├── admin-bookings.md
│   ├── admin-metadata.md
│   ├── admin-csv.md
│   └── hello-oscar-integration.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

**Structure Decision**: Option 2 — Web application, split into an independent `backend/` service (Python
+ FastAPI; owns WhatsApp webhook, LangChain agent, booking rules, Hello Oscar integration, and all admin
APIs, backed by a local SQLite file via SQLAlchemy/Alembic) and an independent `frontend/` React admin
dashboard that only calls `backend`'s admin API surface. This mirrors the required architecture boundary:
the frontend has no path to WhatsApp, LangChain, or Hello Oscar except through backend-issued,
authenticated admin endpoints.

> **Migration note**: An earlier planning pass scaffolded the backend in Node.js/TypeScript with
> Prisma/PostgreSQL and a separate Playwright `e2e/` project. Per this revision's explicit instructions
> (Python/FastAPI/LangChain with a simple local SQLite database, and no e2e suite required), the
> TypeScript backend scaffold and the top-level `e2e/` project have been removed from the repository;
> the `frontend/` React application is unaffected since the frontend stack was not changed by this
> request.

```text
backend/
├── app/
│   ├── webhook/
│   │   ├── webhook_router.py            # POST /webhook-sync entrypoint (FastAPI APIRouter)
│   │   ├── payload_normalizer.py        # normalized-contract + raw SkaleBot mapping
│   │   ├── phone_normalizer.py          # canonical phone format
│   │   └── ownership_detector.py        # handled:true/false decision
│   ├── conversation/
│   │   ├── conversation_session_service.py
│   │   ├── conversation_session_repository.py
│   │   └── idempotency_service.py       # message_id ledger + dedupe
│   ├── agent/
│   │   ├── langchain_agent.py           # agent runner, prompts, tool bindings
│   │   ├── tools/                       # structured tools exposed to the agent
│   │   └── output_schemas.py            # Pydantic schemas the agent must return
│   ├── business_rules/
│   │   ├── booking_state_machine.py     # PROPOSED..UNRESOLVED transitions
│   │   ├── confirmation_rules.py        # explicit-confirmation enforcement
│   │   └── expiry_service.py            # silent proposal expiry
│   ├── booking/
│   │   ├── booking_service.py
│   │   └── booking_repository.py
│   ├── integrations/
│   │   └── hello_oscar/
│   │       ├── hello_oscar_client.py    # adapter interface + impl (contract pending)
│   │       └── hello_oscar_types.py
│   ├── admin/
│   │   ├── auth/                        # login, logout, session validation
│   │   ├── bookings/                    # confirmed bookings read APIs
│   │   ├── metadata/                    # create/update/read business metadata
│   │   └── csv/                         # upload + validation + reporting
│   ├── db/
│   │   ├── models.py                    # SQLAlchemy models
│   │   ├── session.py                   # SQLite engine/session factory
│   │   └── alembic/ (migrations/)
│   ├── shared/
│   │   ├── logging.py
│   │   ├── errors.py
│   │   └── config.py
│   └── main.py                          # FastAPI app factory / ASGI entrypoint
└── tests/
    ├── contract/        # webhook-sync + admin API contract tests (FastAPI TestClient)
    ├── integration/      # conversation flow, booking flow, CSV flow
    └── unit/              # normalizers, state machine, rules, agent tool schemas

frontend/
├── src/
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── BookingsPage.tsx
│   │   ├── MetadataPage.tsx
│   │   └── CsvUploadPage.tsx
│   ├── components/
│   │   ├── bookings/ (BookingList, BookingRow, states: loading/empty/error)
│   │   ├── metadata/ (MetadataForm, field validation messages)
│   │   └── csv/ (CsvUploadForm, ProgressIndicator, ResultSummary)
│   ├── services/
│   │   └── api/ (authApi.ts, bookingsApi.ts, metadataApi.ts, csvApi.ts) # calls backend admin APIs only
│   ├── auth/
│   │   └── AuthContext.tsx, useAuth.ts, ProtectedRoute.tsx
│   └── app/ (routes, App.tsx)
└── tests/
    ├── unit/
    └── integration/
```

## Complexity Tracking

> No Constitution Check violations require justification. This section intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
