---

description: "Brownfield maintenance tasks for approved WhatsApp Meeting Assistant defects"
---

# Tasks: WhatsApp Meeting Assistant Maintenance Fixes

**Input**: Existing implementation and design documents from `/specs/001-whatsapp-meeting-assistant/`

**Scope**: Brownfield fixes only for Azure issues #13, #8, #6 / US1-A2, and #5 / US2-A4. Do not
redesign the full WhatsApp assistant, add browser e2e automation, or change unrelated behavior.

**Stack**: Existing Python/FastAPI, LangChain, SQLAlchemy, SQLite, Pytest, and React/TypeScript code.

**Tests**: Required because each defect has explicit boundary, row-level, or acceptance criteria in the
specification and the existing project test strategy.

---

## Phase 1: Setup and Baseline

**Purpose**: Establish the brownfield baseline before changing defect behavior.

- [X] T001 Run the backend baseline from `backend/` with `source .venv/bin/activate && python -m pytest -q && ruff check app tests`; record current results in the issue work items without changing unrelated code in `backend/`
- [X] T002 [P] Inspect current expiry, CSV, phone-normalization, and complete-message extraction paths in `backend/app/business_rules/expiry_service.py`, `backend/app/admin/csv/`, `backend/app/webhook/phone_normalizer.py`, `backend/app/agent/langchain_agent.py`, and their tests in `backend/tests/`
- [X] T003 [P] Verify isolated SQLite fixtures and migration setup support deterministic clock, mixed-row CSV, and webhook integration tests in `backend/tests/conftest.py`, `backend/app/db/models.py`, and `backend/app/db/session.py`

**Checkpoint**: Existing behavior and reproducible failure inputs are identified for all four Azure issues.

---

## Phase 2: Issue #5 / US2-A4 - Proposal expiry boundary

**Goal**: Expire a proposal exactly at inactivity duration `T` using the authoritative UTC server clock.

**Acceptance criteria**:
- At `T-1`, the proposal remains active.
- At exactly `T`, the proposal is expired and inactive.
- At `T+1`, the proposal remains expired.
- Every valid inbound interaction while active resets the timer from its accepted UTC server timestamp.
- Expiry sends no reminder, triggers no booking, and requires a new proposal.

- [X] T004 [US2] Change expiry comparison to use an injected UTC clock and `elapsed >= T` semantics in `backend/app/business_rules/expiry_service.py`
- [X] T005 [P] [US2] Add unit tests using fixed UTC timestamps for `T-1`, exact `T`, and `T+1`, including persisted naive timestamps, in `backend/tests/unit/test_expiry_service.py`
- [X] T006 [US2] Ensure session loading applies expiry before ownership/confirmation handling and resets `updated_at` after every valid active proposal interaction in `backend/app/conversation/conversation_session_service.py`
- [ ] T007 [P] [US2] Add integration tests proving exact-boundary expiry cannot book or send a reminder and a later interaction starts a new proposal in `backend/tests/integration/test_proposal_expiry_flow.py`

---

## Phase 3: Issue #13 / Issue #8 / US3-A3 - CSV validation and partial success

**Goal**: Process each CSV row according to the authoritative outcome matrix while allowing valid rows to
succeed when other rows fail.

**Acceptance criteria**:
- Valid canonical or accepted international phone numbers produce `CREATED` for new records.
- A valid phone matching an existing record produces `UPDATED`.
- Invalid phone values produce `REJECTED` with row number and field-specific reason.
- A later canonical-equivalent duplicate in the same file produces `SKIPPED` with `duplicate_of_row`.
- Unexpected row processing errors produce row-level `REJECTED` with `processing_error` and do not stop other rows.
- File-level errors reject the upload before any row is written.
- Every data row has exactly one result.
- Final summary contains `total_rows`, `successful_rows`, `created_rows`, `updated_rows`, `failed_rows`, `skipped_rows`, and `row_errors`, with totals matching row outcomes.

- [X] T008 [US3] Reproduce Azure #13 with a valid international phone and capture parser/normalizer input, output, exception, and row number in `backend/tests/contract/test_admin_csv.py`
- [X] T009 [US3] Align CSV phone validation with the shared canonical phone normalizer so valid formats are accepted and invalid values are rejected without raising a whole-upload failure in `backend/app/admin/csv/csv_parser.py` and `backend/app/admin/csv/csv_upload_service.py`
- [X] T010 [US3] Implement the outcome precedence: file-level validation first, row field validation second, canonical duplicate-within-file third, existing-record matching fourth, and row processing error isolation last in `backend/app/admin/csv/csv_upload_service.py`
- [X] T011 [US3] Ensure first canonical phone occurrence creates or updates and later canonical-equivalent rows are skipped without suppressing unrelated valid rows in `backend/app/admin/csv/csv_upload_service.py`
- [X] T012 [US3] Return exact summary counts and row-specific errors required by the CSV matrix, including successful/created/updated/failed/skipped counts, in `backend/app/admin/csv/csv_upload_service.py` and `backend/app/admin/csv/router.py`
- [ ] T013 [P] [US3] Add contract tests for valid phones, invalid phones, mixed rows, existing records, duplicate rows, processing errors, missing headers, malformed files, and exact summary counts in `backend/tests/contract/test_admin_csv.py`
- [ ] T014 [P] [US3] Add integration tests proving valid rows persist alongside invalid rows and `CsvUploadBatch`/`CsvUploadRow` records match the returned summary in `backend/tests/integration/test_csv_mixed_rows.py`

---

## Phase 4: Issue #6 / US1-A2 - Complete WhatsApp message extraction

**Goal**: A complete message containing date, time, and location reaches a proposal without unnecessary follow-up questions.

**Acceptance criteria**:
- Complete, unambiguous meeting details produce no missing meeting fields.
- Date, time, and location are preserved in session context.
- The assistant presents the proposal directly when onboarding data is already known.
- Missing or ambiguous details still produce concise guided prompts.
- Invalid extracted values do not advance the proposal or booking state.
- Agent output cannot confirm a booking or bypass deterministic rules.

- [X] T015 [US1] Reproduce Azure #6 / US1-A2 with representative complete messages containing ISO and natural-language dates, times, and locations in `backend/tests/unit/test_langchain_agent.py`
- [X] T016 [US1] Improve deterministic fallback extraction to capture complete date/time/location messages without consuming trailing text or misclassifying unrelated `at` phrases in `backend/app/agent/langchain_agent.py`
- [X] T017 [US1] Align LangChain structured output and fallback output field names, missing-field behavior, and proposal action semantics in `backend/app/agent/output_schemas.py` and `backend/app/agent/langchain_agent.py`
- [X] T018 [US1] Apply meeting validation immediately after extraction and before `CONFIRMATION_PENDING`, preserving deterministic business-rule authority in `backend/app/webhook/webhook_router.py` and `backend/app/business_rules/meeting_validation.py`
- [X] T019 [P] [US1] Add unit tests for complete extraction, one missing field, ambiguous values, location parsing, natural-language dates, and existing onboarding context in `backend/tests/unit/test_langchain_agent.py`
- [X] T020 [P] [US1] Add integration tests proving a complete message reaches a proposal in one turn and does not ask unnecessary follow-up questions in `backend/tests/integration/test_whatsapp_booking_flow.py`
- [X] T021 [US1] Verify the deterministic confirmation rule remains authoritative when complete agent fields are returned in `backend/tests/unit/test_confirmation_rules.py` and `backend/tests/integration/test_whatsapp_booking_flow.py`

---

## Phase 5: Cross-issue Regression and Delivery

**Purpose**: Prove the approved fixes together and provide Azure work-item evidence.

- [ ] T022 [P] Add regression coverage for complete WhatsApp details followed by explicit confirmation and provider success/failure in `backend/tests/integration/test_whatsapp_booking_flow.py`
- [ ] T023 [P] Add regression coverage for mixed CSV rows with valid, invalid, canonical-equivalent, existing, and unexpected-error outcomes in `backend/tests/integration/test_csv_mixed_rows.py`
- [ ] T024 [P] Add regression coverage for proposal expiry at `T-1`, `T`, and `T+1`, including timer reset after a valid interaction, in `backend/tests/integration/test_proposal_expiry_flow.py`
- [X] T025 Run `python -m pytest -q`, `ruff check app tests`, `python -m compileall -q app tests`, and the frontend build/lint from the repository root; confirm no unrelated regressions in `backend/` and `frontend/`
- [ ] T026 Update Azure DevOps work items #13, #8, #6 / US1-A2, and #5 / US2-A4 with affected paths, validation evidence, and acceptance results in `specs/001-whatsapp-meeting-assistant/`

---

## Dependencies and Execution Order

- Phase 1 precedes all defect work.
- Phase 2, Phase 3, and Phase 4 are independent after Phase 1 and can be assigned separately.
- Phase 5 runs after Phases 2–4 and is the maintenance release gate.
- No task expands the product scope beyond the four approved defect areas.

## Parallel Opportunities

- T002 and T003 can run in parallel.
- T005 and T007 can run in parallel after the expiry implementation contract is fixed.
- T013/T014 and T019/T020 can run in parallel after their corresponding implementation surfaces stabilize.
- T022–T024 can run in parallel after Phases 2–4 complete.

## Suggested MVP Scope

For this maintenance release, implement and validate all four requested Azure issues: #13, #8, #6 / US1-A2, and #5 / US2-A4. No broader feature work is included.
