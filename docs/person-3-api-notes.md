# Person Three trip API and presentation notes

## Completed implementation

The app includes the JSON API in `routes/trips.py` and server-rendered pages
and form routes in `app.py`. `database.py` is the shared Mongo adapter. Data
is persisted through PyMongo; the unit suite uses an in-memory double, and
opt-in integration tests use real MongoDB.

| Operation | Method and endpoint | Response |
| --- | --- | --- |
| List destinations | GET /api/destinations | 200 {"destinations": [...]} |
| Create destination | POST /api/destinations | 201 {"destination": {...}} (admin only) |
| Create trip | POST /api/trips | 201 {"trip": {...}} |
| Read list | GET /api/trips | 200 {"trips": [...]} |
| Read one | GET /api/trips/<id> | 200 {"trip": {...}} |
| Update full editable record | PUT /api/trips/<id> | 200 {"trip": {...}} |
| Delete | DELETE /api/trips/<id> | 200 {"deleted": true} |
| List all users | GET /api/admin/users | 200 {"users": [...]} (admin only) |
| List all trips | GET /api/admin/trips | 200 {"trips": [...]} (admin only) |
| Delete any trip | DELETE /api/admin/trips/<id> | 200 {"deleted": true} (admin only) |

POST and PUT require title, destination_id, start_date, end_date, and budget. destination_id must reference an existing destination in MongoDB. description defaults to an empty string and status defaults to Planned. Status allows Planned, Ongoing, Completed. Dates use YYYY-MM-DD; end cannot precede start. Budget must be a finite nonnegative JSON number, never a boolean. Text is trimmed and bounded. Unknown fields (including _id and user_id) are rejected. PUT replaces every editable field while preserving ownership. Admins can create destinations with name and price through POST /api/destinations.

Example request:

```json
{"title":"Chicago Weekend","destination_id":"64b000000000000000000003","start_date":"2026-11-10","end_date":"2026-11-13","budget":700,"description":"Weekend trip","status":"Planned"}
```

MongoDB stores _id, user_id, and destination_id as ObjectIds. JSON returns them as strings. Trip JSON also includes the referenced destination object. Errors always contain {"error":{"code":"...","message":"..."}}: 400 invalid input/ID, 401 no valid account session, 403 invalid CSRF token or non-admin on an admin route, 404 absent/unowned trip, 409 duplicate destination name, 415 non-JSON body, 503 unavailable database, 500 unexpected failure. Internal exception contents are never returned.

## Authentication and dashboard flow

The homepage form posts to `/` and either logs in against the `users`
collection (Werkzeug password-hash verification) or signs up a new normal user.
The app then clears the session and sets:

- `session["user_id"] = str(user["_id"])`
- `session["user_name"]`
- `session["user_role"]`
- `session["user_email"]`

The app then creates a session CSRF token. User accounts redirect to
`/dashboard`; admin accounts redirect to `/admin`. The dashboard lists the
signed-in user's trips and supports add/edit/delete for owned trips.
Destination changes are intentionally blocked in the edit form. The admin page
supports destination add/price edit/delete (refused while a trip uses it),
lists every user and trip, and can delete any trip.

Use `TRAVELMATE_SECRET_KEY` for signing in normal environments. If it is
missing, the app falls back to a local-development secret so sessions still
work during setup. Never accept a user ID from request JSON as authentication.
Each API route rechecks that the session account still exists in the users
collection.

The factory reads MONGODB_URI and MONGODB_DATABASE (default travelmate) from
environment variables. `database.init_db` exposes
`current_app.extensions["mongo_db"]`. Tests may inject an existing Database
using `MONGO_DB` when creating the app.

## Frontend integration

The dashboard's `static/js/trips.js` uses this API: create is `POST
/api/trips`, edit is `PUT /api/trips/<id>`, delete is `DELETE
/api/trips/<id>`, and after each it reloads the list with `GET /api/trips`.
It reads the CSRF token from the page's hidden form field and sends it in
`X-CSRF-Token` with `Content-Type: application/json`. Other clients can get the
same token from `GET /api/csrf-token` (returned with `Cache-Control: no-store`).
The frontend calls Flask, never MongoDB directly.

## Scope: activities

Trip activities were scoped out. DELETE removes only the trip; there is no
cascade to worry about. If activities are ever added, their routes must verify
the parent trip exists and is owned by the session user.

## Testing and live demo

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Automated tests cover CRUD, repeat reads, owner isolation, unknown/deleted
accounts, destination validation, admin-only destination creation, admin
user/trip listing and trip deletion (API and page), malformed JSON, bad IDs,
CSRF rejection, login/sign-up/logout, dashboard add/edit/delete flows,
destination delete guard, database error redaction, and the homepage without
MongoDB. Two live tests verify persistence across application instances and
idempotent seeding.

Use a dedicated development database: log in as the sample user, create a trip
through the dashboard, edit it, delete it, and confirm the `/api/trips`
responses match the UI (browser DevTools → Network shows each fetch). Then log
in as the sample admin and verify destination management and the user/trip
lists, and that user sessions are denied. Never run destructive tests against
production data.

## Professor question practice

CRUD means Create, Read, Update, Delete. Our methods are POST, GET, PUT, DELETE. create_trip validates JSON, assigns the signed-session owner, calls insert_one and returns 201. list_trips/read_trip query MongoDB and return 200. update_trip uses find_one_and_update with an owner-scoped filter and returns the saved document. delete_trip uses delete_one with the same filter. Both _id and user_id must match for reading, editing or deleting a single trip, so User A cannot access User B's record even if they know its ID. We return 404 in both missing and unowned cases to avoid disclosing other users' data.

The data flow is dashboard form -> trips.js fetch JSON -> Flask blueprint -> session and CSRF checks -> validation -> MongoDB -> JSON response -> trips.js re-renders the cards. To demonstrate, open the corresponding route function and show the owner filter and MongoDB operation.

## Verification evidence

October 7 2026: fourteen unit tests passed on Python 3.12 with Flask 3.1.3 and
PyMongo 4.18.2; live integration tests passed against
mongodb://127.0.0.1:27017.

October 8 2026: all 21 tests (19 unit, 2 live) passed on Python 3.13.5 with
Flask 3.1.2 and PyMongo 4.18.2 against the `travelmate-mongo` Docker container
(mongo:7). In the browser, dashboard create/read/update/delete ran through
`fetch()` without page reloads and persisted across refresh; invalid dates
showed the API error message; admin user/trip lists and trip deletion worked.

To repeat live tests in PowerShell:

```powershell
$env:TRAVELMATE_TEST_MONGODB_URI = "mongodb://127.0.0.1:27017"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use only a development server with permission to create/drop the uniquely named
test database. If the environment variable is absent, the live tests are skipped.
