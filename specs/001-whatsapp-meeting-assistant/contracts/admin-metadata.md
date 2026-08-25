# Contract: Admin Metadata API

Owner: Backend Admin API. Consumed only by the React Admin Dashboard's metadata form.

## `POST /admin/metadata`

Creates or updates a `BusinessMetadata` record depending on the duplicate policy match on
`whatsappPhone` (data-model.md).

**Request**:
```json
{
  "businessName": "Acme Corp",
  "contactPerson": "Jane Doe",
  "whatsappPhone": "+919494151816",
  "address": "123 Main St",
  "sector": "Retail",
  "businessDescription": "Local retail store"
}
```

**Validation rules (server-side, authoritative — client-side validation is a UX convenience only)**:
- `businessName`, `contactPerson`, `whatsappPhone` required, non-empty.
- `whatsappPhone` must normalize to a valid canonical phone number; invalid → field-level error.
- `address`, `sector`, `businessDescription` optional.

**Response (created/updated, 200/201)**:
```json
{
  "id": "uuid",
  "outcome": "CREATED",
  "record": { "...": "the saved BusinessMetadata record" }
}
```
`outcome` is one of `CREATED`, `UPDATED`.

**Response (validation failure, 422)**:
```json
{
  "error": "validation_failed",
  "fieldErrors": {
    "whatsappPhone": "must be a valid phone number",
    "businessName": "is required"
  }
}
```
Invalid records are never persisted (FR-016).

## `PUT /admin/metadata/:id`

Updates an existing record where update is permitted by the approved duplicate/edit policy. Same
validation rules as `POST`. Returns `404` if the record does not exist.

## `GET /admin/metadata` / `GET /admin/metadata/:id`

Read access for the dashboard to list/search existing metadata (supports the "Update metadata" flow,
which needs to find an existing record first).

## Traceability

FR-015, FR-016, FR-019, User Story 3.
