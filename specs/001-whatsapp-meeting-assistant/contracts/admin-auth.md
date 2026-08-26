# Contract: Admin Authentication API

Owner: Backend Admin API. Consumed only by the React Admin Dashboard.

## `POST /admin/auth/login`

**Request**:
```json
{ "email": "admin@example.com", "password": "..." }
```

**Response (success, 200)**: Sets an HttpOnly, Secure, SameSite=Strict session cookie (name TBD, e.g.
`admin_session`). Body contains only non-sensitive profile info:
```json
{ "adminId": "uuid", "email": "admin@example.com" }
```

**Response (failure, 401)**:
```json
{ "error": "invalid_credentials" }
```
Generic error message regardless of whether the email exists, to avoid user enumeration.

## `POST /admin/auth/logout`

Invalidates the current session (server-side session revocation or short-lived token expiry) and clears
the cookie. **Response (200)**: `{ "success": true }`.

## `GET /admin/auth/session`

Used by the frontend on load / route guard to check whether the current cookie represents a valid,
non-expired admin session.

**Response (200, authenticated)**:
```json
{ "authenticated": true, "adminId": "uuid", "email": "admin@example.com" }
```

**Response (200 or 401, not authenticated)**:
```json
{ "authenticated": false }
```

## Cross-cutting rules

- All other admin endpoints (Bookings, Metadata, CSV) require the same valid session; missing/invalid
  session → `401 Unauthorized`, `{ "error": "unauthenticated" }`.
- No admin credential, session token, or signing secret is ever included in any JSON response body.
- Rate limiting / lockout on repeated failed logins is a security hardening item to define during
  implementation (not detailed here to avoid inventing unapproved specifics beyond NFR-003's intent).

## Traceability

Admin Authentication (user request), NFR-003, FR-022.
