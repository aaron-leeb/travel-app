# API and route contract

Everything below is implemented and covered by the test suite. Page routes
return HTML; `/api` routes return JSON.

## Page and form routes (`app.py`)

| Method | Path | Success |
| --- | --- | --- |
| GET | `/` | 200 homepage with login/sign-up and destinations |
| POST | `/` | 302 after login or sign-up; users go to `/dashboard`, admins to `/admin`. Failures re-render with 400 (bad input), 401 (wrong password), 409 (email taken), or 503 (no database) |
| POST | `/logout` | 302 to `/` after clearing the session |
| GET | `/dashboard` | 200 user dashboard (admins are redirected to `/admin`) |
| POST | `/dashboard/trips` | 302 after creating a trip |
| POST | `/dashboard/trips/<id>/edit` | 302 after updating title/dates/budget/description/status |
| POST | `/dashboard/trips/<id>/delete` | 302 after deleting an owned trip |
| GET | `/admin` | 200 admin dashboard (non-admins are redirected to `/dashboard`) |
| POST | `/admin/destinations` | 302 after adding a destination |
| POST | `/admin/destinations/<id>/edit` | 302 after updating a destination price |
| POST | `/admin/destinations/<id>/delete` | 302 after deleting an unused destination; 409 if a trip uses it |
| POST | `/admin/trips/<id>/delete` | 302 after deleting any user's trip |

Form routes redirect to `/` without a session, return 403 for a bad CSRF
token, 400 for invalid input, 404 for missing or unowned records, and 503 when
MongoDB is unavailable.

## JSON API (`routes/trips.py`)

| Method | Path | Success |
| --- | --- | --- |
| GET | `/api/csrf-token` | 200, `{"csrf_token":"..."}` |
| GET | `/api/destinations` | 200, `{"destinations": [...]}` |
| POST | `/api/destinations` | 201, `{"destination": {...}}` (admin only) |
| POST | `/api/trips` | 201, `{"trip": {...}}` |
| GET | `/api/trips` | 200, `{"trips": [...]}`; empty array for no trips |
| GET | `/api/trips/<id>` | 200, `{"trip": {...}}` |
| PUT | `/api/trips/<id>` | 200, `{"trip": {...}}` |
| DELETE | `/api/trips/<id>` | 200, `{"deleted": true}` |
| GET | `/api/admin/users` | 200, `{"users": [...]}` with `_id`, `name`, `email`, `role`, `active` (admin only, no password hashes) |
| GET | `/api/admin/trips` | 200, `{"trips": [...]}` for every user, with `owner_email` and `destination_name` (admin only) |
| DELETE | `/api/admin/trips/<id>` | 200, `{"deleted": true}` for any user's trip (admin only) |

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

Validation rules: title is trimmed nonempty text (max 200); destination_id must
be a valid ObjectId string for an existing destination; dates are valid
YYYY-MM-DD with end >= start; budget is a finite nonnegative number (not a
boolean); description is optional (max 5000); status defaults to Planned and
allows Planned, Ongoing, Completed. Unknown fields, including `_id` and
`user_id`, are rejected. PUT supplies the full editable record. IDs are JSON
strings in `_id`, `user_id`, and `destination_id`, never raw ObjectIds.

Errors use `{"error": {"code": "invalid_input", "message": "..."}}`:

| Status | When |
| --- | --- |
| 400 | Malformed JSON, invalid ID, or failed validation |
| 401 | No session, or the session's account no longer exists |
| 403 | Missing/invalid CSRF token, or a non-admin calling an admin route |
| 404 | Trip does not exist or belongs to another user (same response, to avoid leaking existence) |
| 409 | Destination name already exists |
| 415 | Write request without a JSON content type |
| 503 | MongoDB not configured or unreachable |
| 500 | Unexpected failure; internal details are never returned |

## Authentication and sessions

The homepage form posts to `/` with `auth_action` set to `login` or `signup`.
Login verifies the Werkzeug password hash of an active account; sign-up creates
a new `role="user"` account (never an admin). Either way the app clears the
session and stores:

- `session["user_id"]`
- `session["user_name"]`
- `session["user_role"]`
- `session["user_email"]`

It also creates a session CSRF token. HTML forms send it as a hidden
`csrf_token` field; API writes (POST, PUT, DELETE) send it in `X-CSRF-Token`.
The dashboard's `trips.js` reads it from the page; other clients can call
`GET /api/csrf-token`. Logout requires the token and clears the whole session.

## Authorization

- User trip routes only ever query trips whose `user_id` matches the session
  user, so User A cannot read, edit, or delete User B's trip by ID.
- Admin pages and `/api/admin/*` and `POST /api/destinations` check the stored
  role server-side (`require_admin` / `is_admin`). Non-admins get 403 from the
  API and are redirected away from `/admin`.
- Admin routes are separate from user routes; user routes are never widened to
  bypass owner checks.
- Password hashes are never returned in any response.
- Deleting a trip removes only that trip. Deleting a destination is refused
  while any trip references it.
