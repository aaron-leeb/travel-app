# Trip API contract

The trip blueprint implements this contract. Local MongoDB CRUD/persistence
verification passed, and the current app now includes a server-rendered login
page plus a user dashboard that uses the same signed session as the API.

| Method | Path | Success |
| --- | --- | --- |
| POST | `/` | 302 redirect after form login; user sessions go to `/dashboard`, admin sessions return to `/` |
| GET | `/dashboard` | 200 server-rendered user dashboard |
| POST | `/dashboard/trips` | 302 after creating a trip from the dashboard form |
| POST | `/dashboard/trips/<id>/edit` | 302 after updating title/dates/budget/description/status |
| POST | `/dashboard/trips/<id>/delete` | 302 after deleting an owned trip |
| GET | `/api/csrf-token` | 200, `{"csrf_token":"..."}` |
| GET | `/api/destinations` | 200, `{"destinations": [...]}` |
| POST | `/api/destinations` | 201, `{"destination": {...}}` (admin only) |
| POST | `/api/trips` | 201, `{"trip": {...}}` |
| GET | `/api/trips` | 200, `{"trips": [...]}`; empty array for no trips |
| GET | `/api/trips/<id>` | 200, `{"trip": {...}}` |
| PUT | `/api/trips/<id>` | 200, `{"trip": {...}}` |
| DELETE | `/api/trips/<id>` | 200, `{"deleted": true}` |

Create and PUT requests use `Content-Type: application/json` and fields:

```json
{
  "title": "Chicago Weekend",
  "destination_id": "64b000000000000000000003",
  "start_date": "2026-11-10",
  "end_date": "2026-11-13",
  "budget": 700,
  "description": "Weekend trip",
  "status": "Planned"
}
```

Implemented rules: title is trimmed nonempty text; destination_id must be a valid
ObjectId string for an existing destination; dates are valid YYYY-MM-DD with
end >= start; budget is a finite nonnegative number (not boolean); description
is optional; status defaults to Planned and allows Planned, Ongoing, Completed.
PUT supplies the full editable record. IDs are JSON strings in `_id`,
`user_id`, and `destination_id`, never raw ObjectIds. Do not accept client
ownership changes.

Errors use `{"error": {"code": "invalid_input", "message": "..."}}`.
Use 400 for malformed JSON, invalid IDs, or validation; 401 without a session;
404 for nonexistent or other-user trips (avoid leaking their existence); 415
for a non-JSON write request; 500 for unexpected failures without internal
details. Check session identity before querying owned resources.

## Implemented authentication and session design

The homepage login form posts to `/` using the seeded `users` collection. After
password verification, the app clears the session and stores:

- `session["user_id"]`
- `session["user_name"]`
- `session["user_role"]`
- `session["user_email"]`

The server also creates a session CSRF token. User logins redirect to
`/dashboard`; admin logins return to `/` and can use the admin-only destination
API. There is currently no registration route, logout route, or separate admin
dashboard.

## Authorization and administration

The implemented trip endpoints are available to authenticated sessions only,
and each operation is restricted to trips whose `user_id` matches the session
user. `GET /api/destinations` is also authenticated. `POST /api/destinations`
is admin-only and lets administrators add new destinations with prices.

Potential future admin-only features include managing or deactivating user
accounts, viewing system-wide users/trips, and administering activities. These
should use separate admin routes protected by a server-side role check. Do not
widen the existing user trip routes to bypass owner checks.

## Security/integration decisions

- API reads/writes depend on a signed Flask session and server-side ownership
  checks.
- JSON API writes require `X-CSRF-Token` from `GET /api/csrf-token`.
- Dashboard form writes use the same session CSRF token through hidden form
  fields.
- Agree whether deleting a trip deletes its activities, with Person 5.
- Admin routes are separate and require backend role checks.
- Never return password hashes in user/admin JSON responses.
- Session expiry/rotation/logout policy still needs to be defined if the team
  expands authentication beyond the current demo login.

## Implemented integration interface

See [Person Three notes](person-3-api-notes.md). Authenticated writes require
X-CSRF-Token from GET /api/csrf-token; missing/invalid tokens return 403.
Database configuration/availability errors return 503. The homepage login sets
the session fields after verified login.
The user account is rechecked in MongoDB before each trip request.
DELETE currently removes only the trip; activity cleanup remains a team decision.
