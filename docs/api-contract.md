# Trip API contract

The trip blueprint implements this contract. Local MongoDB CRUD/persistence verification passed. Authentication
and frontend integration are still pending.
Person 3 owns implementation. Person 4 supplies authenticated identity.

| Method | Path | Success |
| --- | --- | --- |
| POST | `/api/trips` | 201, `{"trip": {...}}` |
| GET | `/api/trips` | 200, `{"trips": [...]}`; empty array for no trips |
| GET | `/api/trips/<id>` | 200, `{"trip": {...}}` |
| PUT | `/api/trips/<id>` | 200, `{"trip": {...}}` |
| DELETE | `/api/trips/<id>` | 200, `{"deleted": true}` |

Create and PUT requests use `Content-Type: application/json` and fields:

```json
{
  "title": "Chicago Weekend",
  "destination": "Chicago, IL",
  "start_date": "2026-11-10",
  "end_date": "2026-11-13",
  "budget": 700,
  "description": "Weekend trip",
  "status": "Planned"
}
```

Implemented rules: title/destination are trimmed nonempty strings; dates are valid
YYYY-MM-DD with end >= start; budget is a finite nonnegative number (not boolean);
description is optional; status defaults to Planned and allows Planned,
Ongoing, Completed. PUT supplies the full editable record. IDs are JSON strings
in `_id`/`user_id`, never raw ObjectIds. Do not accept client ownership changes.

Errors use `{"error": {"code": "invalid_input", "message": "..."}}`.
Use 400 for malformed JSON, invalid IDs, or validation; 401 without a session;
404 for nonexistent or other-user trips (avoid leaking their existence); 415
for a non-JSON write request; 500 for unexpected failures without internal
details. Check session identity before querying owned resources.

## Security/integration decisions

- All five routes require authentication and server-side ownership checks.
- Coordinate CSRF protection for session-authenticated writes with Person 4;
  SameSite cookies alone are not the complete policy.
- Agree whether deleting a trip deletes its activities, with Person 5.
- Admin routes are separate and require backend role checks.
- Never return password hashes in user/admin JSON responses.
- Person 4 must define session identity, expiry behavior, database access, and
  helpers before Person 3 finalizes the implementation.

## Implemented integration interface

See [Person Three notes](person-3-api-notes.md). Authenticated writes require
X-CSRF-Token from GET /api/csrf-token; missing/invalid tokens return 403.
Database configuration/availability errors return 503. Person Four must set
session["user_id"] after verified login and clear it on logout.
The user account is rechecked in MongoDB before each trip request.
DELETE currently removes only the trip; activity cleanup remains a team decision.
