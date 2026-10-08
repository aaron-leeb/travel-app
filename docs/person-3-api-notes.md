# Person Three trip API and presentation notes

## Completed implementation

The current app includes both the JSON API in `routes/trips.py` and
server-rendered dashboard flows in `app.py`. `database.py` is the shared Mongo
adapter. Trips are persisted through PyMongo; the unit suite uses an in-memory
double, and opt-in integration tests use real MongoDB.

| Operation | Method and endpoint | Response |
| --- | --- | --- |
| List destinations | GET /api/destinations | 200 {"destinations": [...]} |
| Create destination | POST /api/destinations | 201 {"destination": {...}} (admin only) |
| Create | POST /api/trips | 201 {"trip": {...}} |
| Read list | GET /api/trips | 200 {"trips": [...]} |
| Read one | GET /api/trips/<id> | 200 {"trip": {...}} |
| Update full editable record | PUT /api/trips/<id> | 200 {"trip": {...}} |
| Delete | DELETE /api/trips/<id> | 200 {"deleted": true} |

POST and PUT require title, destination_id, start_date, end_date, and budget. destination_id must reference an existing destination in MongoDB. description defaults to an empty string and status defaults to Planned. Status allows Planned, Ongoing, Completed. Dates use YYYY-MM-DD; end cannot precede start. Budget must be a finite nonnegative JSON number, never a boolean. Text is trimmed and bounded. Unknown fields (including _id and user_id) are rejected. PUT replaces every editable field while preserving ownership. Admins can create destinations with name and price through POST /api/destinations.

Example request:

```json
{"title":"Chicago Weekend","destination_id":"64b000000000000000000003","start_date":"2026-11-10","end_date":"2026-11-13","budget":700,"description":"Weekend trip","status":"Planned"}
```

MongoDB stores _id, user_id, and destination_id as ObjectIds. JSON returns them as strings. Trip JSON also includes the referenced destination object. Errors always contain {"error":{"code":"...","message":"..."}}: 400 invalid input/ID, 401 no valid account session, 403 invalid CSRF token or non-admin destination creation, 404 absent/unowned trip, 409 duplicate destination name, 415 non-JSON body, 503 unavailable database, 500 unexpected failure. Internal exception contents are never returned.

## Implemented authentication and dashboard flow

The homepage login posts to `/` and authenticates against the seeded `users`
collection with Werkzeug password-hash verification. After verifying the
password, the app clears the session and sets:

- `session["user_id"] = str(user["_id"])`
- `session["user_name"]`
- `session["user_role"]`
- `session["user_email"]`

The app then creates a session CSRF token. User accounts redirect to
`/dashboard`; admin accounts return to `/`. The dashboard lists the signed-in
user's trips and supports add/edit/delete actions for owned trips. Destination
changes are intentionally blocked in the dashboard edit form.

Use `TRAVELMATE_SECRET_KEY` for signing in normal environments. If it is
missing, the app falls back to a local-development secret so sessions still
work during setup. Never accept a user ID from request JSON as authentication.
Each API route rechecks that the session account still exists in the users
collection.

The factory reads MONGODB_URI and MONGODB_DATABASE (default travelmate) from
environment variables. `database.init_db` exposes
`current_app.extensions["mongo_db"]`. Tests may inject an existing Database
using `MONGO_DB` when creating the app.

## Person Two frontend handoff

For JSON API writes, call GET `/api/csrf-token` with the same-origin session
cookie. Read `csrf_token` from the JSON and send it in `X-CSRF-Token` on POST,
PUT, and DELETE. Send `Content-Type: application/json` for POST and PUT. This
token is session-specific and the endpoint returns `Cache-Control: no-store`.

For the server-rendered dashboard, the app already injects the same CSRF token
into hidden form fields. The frontend calls Flask, never MongoDB directly.

## Person Five activities handoff

DELETE currently removes only the owned trip. Agree on activity cleanup before merging activities; this implementation does not claim cascade deletion. Activity routes must verify the parent trip still exists and is owned. Admin routes remain separate and require Person Four's role protection.

## Testing and live demo

Run: .venv\Scripts\python.exe -m unittest discover -s tests -v

Automated tests cover CRUD, repeat reads, owner isolation, unknown/deleted
accounts, destination validation, admin-only destination creation, malformed
JSON, bad IDs, CSRF rejection, dashboard login redirect, dashboard add/edit/
delete flows, database error redaction, and the homepage without MongoDB. A
separate live test verifies persistence across application instances.

Use a dedicated development database: log in as the sample user, create a trip
through the dashboard, edit it, delete it, and confirm the `/api/trips`
responses match the UI. Then log in as the sample admin and verify destination
creation succeeds while user sessions are denied. Never run destructive tests
against production data.

## Professor question practice

CRUD means Create, Read, Update, Delete. Our methods are POST, GET, PUT, DELETE. create_trip validates JSON, assigns the signed-session owner, calls insert_one and returns 201. list_trips/read_trip query MongoDB and return 200. update_trip uses find_one_and_update with an owner-scoped filter and returns the saved document. delete_trip uses delete_one with the same filter. Both _id and user_id must match for reading, editing or deleting a single trip, so User A cannot access User B's record even if they know its ID. We return 404 in both missing and unowned cases to avoid disclosing other users' data.

The data flow is form -> JavaScript fetch JSON -> Flask blueprint -> session and CSRF checks -> validation -> MongoDB -> JSON response -> frontend. To demonstrate, open the corresponding route function and show the owner filter and MongoDB operation.

## Verification evidence October 7 2026

Fourteen unit tests passed on Python 3.12 with Flask 3.1.3 and PyMongo 4.18.2.
The live integration tests connected to mongodb://127.0.0.1:27017, created
uniquely named temporary test databases, verified create/read across separate
Flask instances, and verified idempotent seeding of users, destinations, and
the sample trip. Homepage password login and the dashboard flows are now
implemented in the app.

To repeat live tests in PowerShell:

```powershell
$env:TRAVELMATE_TEST_MONGODB_URI = "mongodb://127.0.0.1:27017"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use only a development server with permission to create/drop the uniquely named
test database. If the environment variable is absent, the live test is skipped.
