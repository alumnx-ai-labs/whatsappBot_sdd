<!--
Sync Impact Report
- Version change: placeholder -> 1.0.0
- Modified principles: placeholder principles -> I-XX, all newly defined for WhatsApp meeting scheduling
- Added sections: Product Constraints; Delivery Workflow
- Removed sections: none
- Follow-up TODOs: confirm the original constitution ratification date
-->

# WhatsApp Meeting Scheduling Bot Constitution

## Core Principles

### I. Requirements Before Implementation
Business requirements MUST be validated and approved before functionality is implemented. Each
requirement MUST identify its intended user outcome and boundaries so that implementation does not
silently invent product behavior.

### II. No False Booking Confirmation
The system MUST never confirm a meeting to a user unless Hello Oscar has successfully confirmed the
booking. A failed, timed-out, ambiguous, or unverified provider response MUST be communicated as
unconfirmed.

### III. Explicit State Management
Important business operations MUST use clear, deterministic, and testable states. State transitions
MUST define valid inputs, outputs, and failure behavior so retries cannot create implicit outcomes.

### IV. External API Contract First
Every external API integration MUST have a documented request, response, error, timeout, and retry
contract before implementation. Contract validation MUST cover the provider behavior relied upon by
booking and availability workflows.

### V. Human-Readable Conversations
WhatsApp responses MUST be concise, natural, and understandable to a non-technical user. Messages
MUST state the current outcome and the next useful action without exposing internal implementation
details.

### VI. User Confirmation Before Booking
The bot MUST present the appointment details and obtain explicit user confirmation before committing
the booking. It MUST NOT infer confirmation from silence, an ambiguous reply, or unrelated text.

### VII. Fail Safely
Failures MUST be reported truthfully, preserve data integrity, and provide a recovery path when one
is available. Partial or uncertain operations MUST remain distinguishable from successful operations.

### VIII. Idempotency and Duplicate Protection
Retries, repeated messages, and duplicate webhook deliveries MUST NOT create duplicate bookings or
records. Booking and persistence operations MUST use stable idempotency keys or equivalent duplicate
protection.

### IX. Security by Default
Credentials, customer data, administrative access, and system communications MUST be protected by
default. Secrets MUST NOT appear in source, logs, user messages, or test fixtures, and access MUST be
limited to the minimum required scope.

### X. Minimal MVP Scope
The MVP MUST prioritize only functionality required for reliable WhatsApp meeting scheduling and
booking visibility. Enhancements outside that workflow require explicit approval and MUST NOT weaken
the core reliability guarantees.

### XI. Testable Requirements
Every significant requirement MUST have objectively verifiable acceptance criteria. Tests MUST cover
success, rejection, retry, provider failure, and ambiguous-input paths where those paths apply.

### XII. End-to-End Traceability
Every implementation task MUST trace from a business requirement to acceptance criteria and tests.
Missing traceability is a release-blocking quality gap because it prevents proving that approved needs
were delivered.

### XIII. Single Source of Truth
The latest approved specification is authoritative for product behavior. Code, tests, and operational
documentation MUST be brought into alignment when the approved specification changes.

### XIV. Controlled Requirement Changes
Requirement changes MUST be assessed for product, data, integration, security, and test impact before
implementation. The approved change and its impact MUST be documented in the relevant design
artifacts.

### XV. Observable Operations
The system MUST log enough structured information to diagnose conversations, bookings, integrations,
failures, and state transitions. Logs MUST support correlation without exposing credentials or
unnecessary sensitive customer data.

### XVI. Separation of Responsibilities
Conversation handling, business rules, data access, booking orchestration, external integrations, and
administration MUST remain logically separated. Each responsibility MUST have a clear ownership
boundary and independently testable behavior.

### XVII. AI Cannot Override Business Rules
AI MAY interpret user language and propose structured intent, but deterministic business and
transactional rules MUST decide eligibility, confirmation, booking, and failure outcomes. AI output
MUST be treated as untrusted input at those boundaries.

### XVIII. Data Minimization
The system MUST collect and retain only customer data required for the approved business workflow.
Retention, access, and deletion behavior MUST be documented for every retained data category.

### XIX. Definition of Done
Work is complete only when requirements, acceptance criteria, testing, security, documentation, and
constitutional rules are satisfied. A feature that works on the happy path but lacks required failure
or security validation is incomplete.

### XX. Reliable Booking Visibility
Booking visibility MUST reflect the authoritative booking outcome and distinguish confirmed,
unconfirmed, cancelled, and failed states. Users and administrators MUST NOT be shown a successful
booking state based solely on a local intent or pending request.

## Product Constraints

The product is a WhatsApp-based meeting scheduling workflow integrated with Hello Oscar. The system
MUST support clear availability and appointment-detail conversations, explicit user confirmation,
provider-confirmed booking, and trustworthy booking visibility. Provider contracts, webhook handling,
state persistence, and administrative access MUST respect the principles above.

## Delivery Workflow

Before implementation, the team MUST approve the specification, document external contracts, define
state transitions, and map requirements to acceptance criteria and tests. Reviews MUST verify
traceability, security, idempotency, observability, and failure handling. Release approval MUST be
blocked by unresolved critical contract, booking-integrity, or security failures.

## Governance

This constitution governs product behavior, implementation planning, reviews, and release decisions.
When another practice conflicts with it, this constitution takes precedence unless it is formally
amended.

Amendments MUST include the proposed text, rationale, affected requirements and artifacts, migration
or compatibility impact, and updated tests or review criteria. The amendment MUST be approved before
dependent implementation begins. The latest approved constitution and specification MUST be used as
the basis for compliance review.

Versions follow semantic versioning. A MAJOR increment denotes backward-incompatible governance
changes, including principle removal or redefinition. A MINOR increment denotes a new principle or
materially expanded governance section. A PATCH increment denotes clarification, wording, or typo
changes without semantic effect.

Every implementation review MUST check constitutional compliance and requirement traceability.
Compliance review MUST include booking confirmation integrity, state transitions, duplicate
protection, security, data minimization, observability, and test evidence. Exceptions MUST be
documented, approved by the project owner, and time-limited.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-08-24
