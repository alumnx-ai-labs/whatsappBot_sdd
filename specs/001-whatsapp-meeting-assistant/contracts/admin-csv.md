# Contract: Admin CSV Upload API

Owner: Backend Admin API. Consumed only by the React Admin Dashboard's CSV upload page.

## `POST /admin/metadata/csv` (multipart/form-data)

**Request**: multipart form with a single `file` field (`.csv`, UTF-8 encoded). Enforced limits (default,
adjustable via config — see research.md item 10): max file size, max row count. Files exceeding limits
are rejected outright without partial processing.

**Required CSV header schema** (business/customer metadata, matching `BusinessMetadata` fields):

```text
businessName,contactPerson,whatsappPhone,address,sector,businessDescription
```

- `businessName`, `contactPerson`, `whatsappPhone` required per row.
- `address`, `sector`, `businessDescription` optional (empty cell allowed).
- Extra/unknown columns → row is still processed using only recognized columns, but the response
  surfaces a warning noting ignored columns (does not silently accept unapproved schema drift).
- Missing required headers → whole file rejected before any row processing:
  ```json
  { "error": "invalid_schema", "missingHeaders": ["whatsappPhone"] }
  ```

## Processing model

Synchronous processing per research.md item 10: the request handler parses, validates every row, applies
the same deterministic duplicate policy as single-entry (`admin-metadata.md`), and returns one complete
report. No rows are silently discarded; every row appears in the report with an outcome.

**Response (200)**:
```json
{
  "batch_id": "uuid",
  "total_rows": 10,
  "successful_rows": 8,
  "created_rows": 6,
  "updated_rows": 2,
  "failed_rows": 1,
  "skipped_rows": 1,
  "row_errors": [
    { "row_number": 4, "errors": { "whatsappPhone": "must be a valid phone number" } }
  ],
  "rows": [
    { "row_number": 2, "outcome": "CREATED" },
    { "row_number": 3, "outcome": "UPDATED" },
    { "row_number": 4, "outcome": "REJECTED", "errors": { "whatsappPhone": "must be a valid phone number" } },
    { "row_number": 5, "outcome": "SKIPPED", "reason": "duplicate of row 2 within this file", "duplicate_of_row": 2 }
  ]
}
```

- `outcome` values are exactly `CREATED`, `UPDATED`, `SKIPPED`, and `REJECTED` (FR-019).
- Row numbers are 1-based and match the source file, with the header as row 1 and data beginning at row 2.
- `successful_rows` equals `created_rows + updated_rows`; `failed_rows` equals rejected rows; and
  `skipped_rows` equals skipped duplicates. These totals MUST equal the row-level outcomes.
- `row_errors` contains every rejected row number and its field-specific validation or processing error.
- The first valid canonical phone occurrence is processed. Later canonical-equivalent rows are `SKIPPED`
  and include `duplicate_of_row`.
- A valid row matching an existing system record is `UPDATED`.
- Unexpected row processing errors reject only the affected row and do not prevent valid rows from being
  committed. This is the authoritative partial-success policy.
- File-level errors (empty, undecodable, malformed, oversized, or missing required headers) reject the
  entire upload before any row is committed.

## Upload progress (frontend behavior)

Because processing is synchronous per research.md item 10, "upload progress" in the UI reflects (a) file
transfer/upload progress (native `XMLHttpRequest`/`fetch` upload progress event) and (b) a
processing/loading indicator while awaiting the server's validation report — there is no separate
async job-status endpoint for the MVP.

## Error handling

- Malformed CSV (unparseable, wrong encoding): `400`, `{ "error": "malformed_csv" }`, no rows processed.
- Empty file: `400`, `{ "error": "empty_file" }`.
- Oversized file/row count: `413`, `{ "error": "file_too_large", "maxBytes": ..., "maxRows": ... }`.
- Unauthorized: `401` (see admin-auth.md).

## Traceability

FR-017, FR-018, FR-019, User Story 3, spec CSV Requirements, spec Edge Cases (empty/malformed/oversized
CSV).
