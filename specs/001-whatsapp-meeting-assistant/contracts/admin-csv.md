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
  "batchId": "uuid",
  "totalRows": 10,
  "accepted": 8,
  "rejected": 2,
  "rows": [
    { "rowNumber": 2, "outcome": "CREATED" },
    { "rowNumber": 3, "outcome": "UPDATED" },
    { "rowNumber": 4, "outcome": "REJECTED", "reason": "whatsappPhone is not a valid phone number" },
    { "rowNumber": 5, "outcome": "SKIPPED", "reason": "duplicate of row 2 within this file" }
  ]
}
```

- `outcome` values: `CREATED`, `UPDATED`, `SKIPPED`, `REJECTED` (matches FR-019).
- Row numbers are 1-based and match the source file, counting the header row as row 1 (so data rows
  start at row 2) — exact convention MUST be confirmed and documented in the final approved CSV contract,
  but numbering MUST be stable and traceable back to the file as submitted (FR-018).
- Partial success policy: valid rows are committed even if other rows in the same file are rejected,
  consistent with the spec's stated default assumption (subject to final approval, spec Open item).

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
