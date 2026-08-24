# Feature Specification: WhatsApp Meeting Assistant

**Feature Branch**: `001-whatsapp-meeting-assistant`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Build a greenfield WhatsApp Meeting Assistant for businesses."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visitor schedules a confirmed meeting (Priority: P1)

A visitor contacts a business through WhatsApp, is recognized or onboarded, provides meeting details,
reviews a proposed appointment, confirms it, and receives the actual booking outcome. A meeting is
presented as confirmed only after Hello Oscar confirms successful creation.

**Why this priority**: This is the primary business outcome and the smallest complete customer journey
that reduces manual scheduling effort while protecting booking integrity.

**Independent Test**: Using a test WhatsApp conversation and a controlled scheduling service, verify a
returning and a new visitor can reach a confirmed booking, and verify provider failure never produces a
confirmation.

**Acceptance Scenarios**:

1. **Given** a returning visitor with an existing record, **When** they request a meeting and provide
   valid details, **Then** the assistant greets them by the stored name and presents the proposed details
   for explicit confirmation.
2. **Given** a new visitor, **When** they provide the required onboarding information and meeting
   details, **Then** the assistant stores the visitor information and presents the proposed appointment
   for confirmation.
3. **Given** a visitor has explicitly confirmed the proposed details, **When** Hello Oscar returns a
   successful booking result, **Then** the system stores the external booking identifier and tells the
   visitor the meeting is confirmed.
4. **Given** a visitor has explicitly confirmed the proposed details, **When** Hello Oscar rejects,
   times out, or returns an ambiguous result, **Then** the system does not mark the booking confirmed,
   tells the visitor it was not confirmed, records the failure or uncertainty, and offers recovery.

---

### User Story 2 - Visitor corrects or abandons a proposal (Priority: P1)

A visitor can modify appointment details before booking or stop responding without an unintended booking.

**Why this priority**: Explicit confirmation and safe recovery prevent incorrect appointments and are
non-negotiable business rules for the primary journey.

**Independent Test**: Present a proposed appointment, submit a modification, cancellation, ambiguous
reply, and no reply, and verify each path leaves the booking unconfirmed until a later explicit
confirmation.

**Acceptance Scenarios**:

1. **Given** a proposal is awaiting confirmation, **When** the visitor changes the date, time, or
   location, **Then** the system updates the proposal and presents the revised details without booking.
2. **Given** a proposal is awaiting confirmation, **When** the visitor sends an ambiguous response,
   **Then** the system asks for an unambiguous confirmation or modification and does not book.
3. **Given** a proposal is awaiting confirmation, **When** the visitor stops responding, **Then** the
   system does not book and retains an unconfirmed state for the defined recovery period.

---

### User Story 3 - Administrator manages business and customer metadata (Priority: P2)

An authorized business user can add or update metadata through a single-entry form and bulk CSV upload,
with validation and deterministic duplicate handling.

**Why this priority**: Accurate metadata enables personalized conversations and supports operational
setup across many records.

**Independent Test**: As an authorized administrator, submit valid and invalid single records and a CSV
containing valid, invalid, duplicate, and existing records, then verify the documented outcomes and
error report.

**Acceptance Scenarios**:

1. **Given** an authorized administrator submits a valid single record, **When** the record is saved,
   **Then** the system creates or updates it according to the duplicate policy and reports the result.
2. **Given** an administrator submits incomplete or invalid metadata, **When** validation runs,
   **Then** the record is not stored and field-level errors identify the corrections required.
3. **Given** a valid CSV contains both valid and invalid rows, **When** it is uploaded, **Then** valid
   rows are processed according to the partial-success policy, invalid rows are rejected with row-level
   reasons, and the administrator receives a summary.

---

### User Story 4 - Administrator monitors confirmed bookings (Priority: P2)

An authorized business user can view confirmed bookings, see the customer and appointment details, and
refresh the list to observe newly confirmed meetings.

**Why this priority**: Booking visibility gives staff confidence that automated scheduling produced real,
provider-confirmed appointments.

**Independent Test**: Seed confirmed, failed, pending, and cancelled outcomes, open the booking view,
and verify only the defined confirmed set is shown with the required fields; refresh after a new
confirmation and verify it appears.

**Acceptance Scenarios**:

1. **Given** confirmed bookings exist, **When** an authorized administrator opens the booking view,
   **Then** each displayed booking shows who the meeting is with, date, time, location, creation time,
   and status.
2. **Given** a new booking becomes confirmed after the view loads, **When** the administrator refreshes,
   **Then** the refreshed list includes the new confirmed booking.
3. **Given** a booking is failed, pending, or unconfirmed, **When** the administrator views confirmed
   bookings, **Then** it is not presented as confirmed.

### Edge Cases

- A message arrives more than once or a WhatsApp webhook is delivered more than once; processing is
  idempotent and does not duplicate records or bookings.
- A visitor's phone number is missing, malformed, or associated with more than one possible customer;
  the system does not guess and requests the information or routes to the defined recovery path.
- A visitor provides an incomplete, invalid, past, or unavailable date or time; the system explains the
  issue and requests valid alternatives without booking.
- A visitor requests a location that is not supported or omits a required location; the system asks for
  a valid location and keeps the proposal unconfirmed.
- WhatsApp delivery fails after an inbound message is processed; persisted state prevents unsafe
  reprocessing and supports retrying the response.
- Hello Oscar is unavailable, slow, rejects a request, returns malformed data, or confirms externally
  while the application loses the response; the local record remains non-confirmed until the result is
  authoritatively reconciled.
- A CSV is empty, malformed, encoded unexpectedly, has missing headers, extra columns, duplicate rows,
  invalid values, or exceeds the supported size; the upload response identifies whether no rows or only
  affected rows were processed.
- An administrator loses authorization during an operation; the operation is denied and no partial
  unauthorized change is exposed.
- Logs, error messages, exports, and admin screens must not expose credentials or unnecessary personal
  data.

## Requirements *(mandatory)*

### Confirmed Requirements

- The MVP is a WhatsApp conversational assistant for business meeting requests.
- It identifies returning visitors, onboards new visitors, collects meeting details, obtains explicit
  confirmation, books through Hello Oscar, and shows confirmed bookings to authorized administrators.
- The existing flow diagram and admin UI are reference material only and do not override this
  specification.
- The MVP excludes marketing campaigns, promotional messaging, payments, CRM, advanced analytics,
  lead scoring, voice calling, complex reporting, multi-tenant SaaS management, and advanced calendar
  administration.

### Functional Requirements

- **FR-001**: The system MUST receive incoming WhatsApp messages and associate each message with a
  conversation context.
- **FR-002**: The system MUST identify a returning visitor using the approved unique identifier and
  MUST use the stored name for a personalized greeting when available.
- **FR-003**: The system MUST recognize a new visitor and collect the approved mandatory onboarding
  fields before proceeding with a meeting request.
- **FR-004**: The system MUST identify meeting intent and collect the required date, time, and location
  information where applicable.
- **FR-005**: The system MUST validate visitor, business, and meeting data before advancing the
  conversation.
- **FR-006**: The system MUST summarize the proposed appointment, including date, time, location, and
  relevant business/customer details, before booking.
- **FR-007**: The system MUST accept explicit confirmation or modification and MUST keep the proposal
  unbooked for any ambiguous or unrelated response.
- **FR-008**: The system MUST send a booking request to Hello Oscar only after explicit visitor
  confirmation and valid required details.
- **FR-009**: The system MUST wait for and validate the Hello Oscar result before declaring a booking
  confirmed.
- **FR-010**: The system MUST store a booking as confirmed only when Hello Oscar provides a definitive
  successful result and an external booking identifier when required by the approved contract.
- **FR-011**: The system MUST never tell a visitor that a meeting is confirmed based solely on local
  intent, a submitted request, an AI interpretation, or an uncertain provider response.
- **FR-012**: The system MUST record failed, rejected, timed-out, and unresolved booking attempts with
  a non-confirmed outcome and provide an understandable recovery path.
- **FR-013**: The system MUST protect booking and message processing from repeated messages, retries,
  and duplicate webhook deliveries.
- **FR-014**: The system MUST provide clear, concise, natural WhatsApp responses for success,
  confirmation, modification, invalid input, unavailable slots, failure, and recovery paths.
- **FR-015**: The system MUST provide an authorized administrator with a single-entry form for business
  and customer metadata.
- **FR-016**: The system MUST validate single-entry metadata and MUST NOT store invalid or incomplete
  records.
- **FR-017**: The system MUST support bulk metadata upload through CSV using the approved schema and
  validation rules.
- **FR-018**: The system MUST report CSV results by row, including accepted, rejected, duplicate, and
  processing-error outcomes, according to the approved partial-success policy.
- **FR-019**: The system MUST apply one deterministic policy to duplicate CSV rows and existing-record
  matches, and MUST report whether each record was created, updated, skipped, or rejected.
- **FR-020**: The system MUST allow an authorized administrator to view confirmed bookings and show
  customer, business, date, time, location, creation time, and booking status.
- **FR-021**: The system MUST allow an authorized administrator to refresh the confirmed-booking view.
- **FR-022**: The system MUST enforce authorized access for administrative operations and protect
  customer and booking information.
- **FR-023**: The system MUST record sufficient observable events for inbound interactions, visitor
  identification, booking attempts, provider results, failures, and important state transitions without
  unnecessarily exposing sensitive data.
- **FR-024**: The system MUST keep conversation interpretation separate from deterministic business
  and transactional rules; AI output MUST NOT directly set booking state or override validation.
- **FR-025**: The system MUST support reconciliation of uncertain external outcomes before displaying
  a booking as confirmed.

### Non-Functional Requirements

- **NFR-001 Reliability**: Duplicate deliveries and retryable failures MUST be safe to replay without
  duplicate bookings or records.
- **NFR-002 Integrity**: No user-facing or administrative confirmed status may appear before authoritative
  Hello Oscar confirmation.
- **NFR-003 Security**: Administrative access MUST be restricted to authorized users; credentials MUST
  remain outside user-facing clients and logs; communications MUST use secure transport.
- **NFR-004 Privacy**: The system MUST collect, display, and retain only approved data required for the
  workflow, with retention and deletion behavior documented before release.
- **NFR-005 Usability**: At least 90% of representative users in acceptance testing MUST understand the
  next action after each primary-path response without staff explanation.
- **NFR-006 Observability**: Every booking attempt MUST be traceable across conversation, local state,
  external request, external result, and final user-visible outcome using a non-sensitive correlation
  reference.
- **NFR-007 Performance**: For available local operations, 95% of user-facing responses MUST be issued
  within 5 seconds, excluding documented third-party delays; users MUST receive a truthful progress or
  recovery message when that target cannot be met.

### Business Rules

1. A booking is confirmed only after definitive successful confirmation from Hello Oscar.
2. Explicit visitor confirmation is required before every booking request.
3. AI may interpret language but cannot override deterministic rules or set transactional state.
4. The approved unique visitor identifier determines returning-user recognition.
5. Duplicate messages, retries, and repeated webhooks cannot create duplicate bookings or records.
6. Invalid or incomplete metadata cannot be stored.
7. Confirmed-booking visibility reflects the authoritative booking outcome, not a pending request.
8. Any change to these rules requires documented impact assessment and approval.

### State Model

The system MUST represent the booking lifecycle with these deterministic states:

- **PROPOSED**: Required meeting details are being collected or have been drafted; no confirmation
  request has been made.
- **CONFIRMATION_PENDING**: A complete appointment summary has been presented and explicit visitor
  confirmation is awaited; no booking request has been sent.
- **BOOKING_IN_PROGRESS**: Explicit confirmation was received and a single idempotent booking attempt
  is being resolved by Hello Oscar.
- **CONFIRMED**: Hello Oscar definitively confirmed creation and supplied the authoritative booking
  result; this is the only state shown as confirmed.
- **FAILED**: The booking was rejected, timed out, malformed, or otherwise not confirmed; recovery may
  begin from this state.
- **CANCELLED**: A previously confirmed booking was cancelled by an approved actor and is not an active
  confirmed appointment.
- **UNRESOLVED**: The application cannot determine the external outcome; it MUST remain non-confirmed
  until reconciliation resolves it to CONFIRMED or FAILED.

Every transition MUST be caused by a recorded business event, MUST be idempotent, and MUST have a
verifiable test for valid and invalid transitions.

### External Integration Requirements

Hello Oscar is the authoritative source for successful meeting creation. Before implementation, the
team MUST document and obtain approval for the Hello Oscar API base URL, authentication, endpoints,
request and response schemas, availability behavior, error responses, timezone handling, external
booking identifier, cancellation/rescheduling capabilities, timeout behavior, retry behavior, and
reconciliation behavior. This specification intentionally does not invent those contract details.

The WhatsApp integration contract MUST define inbound message identity, delivery acknowledgement,
message types, outbound response rules, delivery failures, webhook authenticity, retry behavior, and
idempotency expectations before implementation.

### Data Requirements

The system will manage these conceptual entities:

- **Customer/Visitor**: Customer identifier, name, WhatsApp phone number, business name, contact
  information, creation timestamp, and last interaction timestamp.
- **Business Metadata**: Business name, contact person, WhatsApp phone number, address, sector, and
  business description.
- **Booking**: Booking identifier, customer identifier, customer name, business name, meeting date,
  meeting time, location, booking status, external Hello Oscar booking identifier, created timestamp,
  and updated timestamp.
- **Conversation**: Conversation identity, current interaction state, inbound and outbound message
  references, timestamps, and non-sensitive processing outcome needed for recovery and traceability.

The WhatsApp phone number is the unique visitor/business identifier: one phone number maps to one
visitor/business record. Name and business name are mandatory for new visitors; contact information
is optional unless required by the approved business workflow. The system MUST define and document
retention, deletion, privacy obligations, and audit evidence before release.

### CSV Requirements

The CSV contract MUST define a header-based schema for business/customer metadata, field formats,
required fields, encoding, maximum file and row limits, normalization, and allowed values. The upload
MUST validate each row before storage, identify row numbers in errors, reject malformed files safely,
and apply the same deterministic duplicate policy as single-entry updates. The approved contract MUST
state whether valid rows are committed when other rows fail; until then, the default assumption is
partial success with an explicit result report and no silent row loss.

### Security and Privacy Requirements

The system MUST authenticate and authorize administrators through a single administrator role, validate
inbound data and webhook provenance, keep credentials outside frontend code, use secure communications,
protect customer and booking information, and avoid secrets or unnecessary personal data in logs.
Collection and retention MUST be limited to operational data required for the approved workflow. A
documented deletion process MUST be defined and approved before release, including conversation history,
customer data, booking data, and audit evidence.

### MVP Scope

**In scope**: Incoming and outgoing WhatsApp conversations; visitor identification; returning-visitor
recognition and greeting; new-visitor onboarding; meeting request handling; date, time, and applicable
location collection; appointment confirmation; Hello Oscar scheduling; confirmed and failed booking
handling; persistence; business/customer metadata entry and updates; CSV upload; confirmed-booking
view; refresh; security, observability, and duplicate protection required for these workflows.

**Out of scope**: WhatsApp marketing campaigns; bulk promotional messaging; payment processing; CRM
functionality; advanced analytics; lead scoring; voice calling; complex reporting; multi-tenant SaaS
management; advanced calendar administration; and automated marketing campaigns.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of representative returning visitors complete the primary scheduling flow
  without staff intervention.
- **SC-002**: At least 90% of representative new visitors provide all approved mandatory onboarding
  information and reach a valid appointment proposal without staff intervention.
- **SC-003**: 100% of bookings shown as confirmed have a matching definitive Hello Oscar success result
  and external booking identifier where the approved contract requires one.
- **SC-004**: 0 provider failures, timeouts, ambiguous responses, or unresolved outcomes are presented
  to visitors or administrators as confirmed bookings during acceptance testing.
- **SC-005**: 100% of repeated messages, retried booking attempts, and duplicate webhook deliveries in
  the acceptance suite produce at most one confirmed booking and one corresponding confirmed record.
- **SC-006**: Authorized administrators can locate and refresh a confirmed booking, including all
  required details, in under 30 seconds in 90% of acceptance tests.
- **SC-007**: At least 95% of representative local user-facing responses are issued within 5 seconds,
  excluding documented external-provider delays.
- **SC-008**: CSV acceptance tests report 100% of invalid rows with a row-specific reason and do not
  silently discard any submitted row.
- **SC-009**: At least 90% of representative users correctly identify the next action after primary-path
  WhatsApp responses without staff explanation.
- **SC-010**: All released functional requirements have linked acceptance scenarios and test evidence
  before the MVP is approved.

## Assumptions

- Required WhatsApp capabilities and permissions will be available for inbound and outbound messaging.
- Hello Oscar provides a supported meeting scheduling service and a definitive success/failure result,
  but its contract details are not assumed until documented and approved.
- A business has one or more defined meeting locations or an approved way to collect a location.
- Administrators are pre-authorized business users; the authentication mechanism remains to be selected.
- The MVP has one administrator role; finer-grained administrator roles are out of scope.
- Only operational data needed to support conversations, bookings, administration, recovery, and audit
  is retained, subject to the approved deletion process.
- Stable internet connectivity is available to visitors and administrators, subject to normal delivery
  failures.
- The MVP focuses on scheduling and booking visibility, not general-purpose customer support.
- Natural-language date and time parsing may be supported only where it can be validated unambiguously;
  otherwise the assistant requests a clearer value.
- Booking cancellation and rescheduling are excluded from the initial happy path unless required by
  the approved Hello Oscar contract or a stakeholder decision.
- The default CSV policy is partial success with explicit row-level reporting, subject to approval.
- The Hello Oscar contract will be supplied and approved before planning; no provider contract behavior
  is inferred in this specification.

## Open Questions

1. **Hello Oscar contract and booking recovery**: The contract will be supplied separately and MUST be
  approved before planning. It must define the base URL, authentication, endpoints, schemas,
  availability behavior, timezone, timeout/retry rules, cancellation/rescheduling support, and
  reconciliation behavior after a lost response.
2. **Deletion implementation details**: The single administrator role and operational-data-only
  retention policy are approved. The specific deletion schedule, deletion triggers, and treatment of
  legally required audit evidence MUST be defined before release.

## Traceability

Each functional requirement MUST map to one or more user-story acceptance scenarios and corresponding
verification evidence in the implementation plan. The approved specification is the single source of
truth for that mapping; requirement changes require impact assessment before implementation.
