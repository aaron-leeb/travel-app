# Person Three trip API and presentation notes

## Completed implementation

Person Three owns routes/trips.py and tests/test_trips.py. The factory in app.py registers the blueprint. database.py is a small shared adapter for Person Four to reuse or replace with their agreed connection helper. Trips are persisted through PyMongo; the unit suite uses an in-memory double, and an opt-in integration test uses real MongoDB.

| Operation | Method and endpoint | Response |
| --- | --- | --- |
| Create | POST /api/trips | 201 {"trip": {...}} |
| Read list | GET /api/trips | 200 {"trips": [...]} |
| Read one | GET /api/trips/<id> | 200 {"trip": {...}} |
| Update full editable record | PUT /api/trips/<id> | 200 {"trip": {...}} |
| Delete | DELETE /api/trips/<id> | 200 {"deleted": true} |

POST and PUT require title, destination, start_date, end_date, and budget. description defaults to an empty string and status defaults to Planned. Status allows Planned, Ongoing, Completed. Dates use YYYY-MM-DD; end cannot precede start. Budget must be a finite nonnegative JSON number, never a boolean. Text is trimmed and bounded. Unknown fields (including _id and user_id) are rejected. PUT replaces every editable field while preserving ownership.

Example request:

```json
{"title":"Chicago Weekend","destination":"Chicago, IL","start_date":"2026-11-10","end_date":"2026-11-13","budget":700,"description":"Weekend trip","status":"Planned"}
```

MongoDB stores _id and user_id as ObjectIds. JSON returns both as strings. Errors always contain {"error":{"code":"...","message":"..."}}: 400 invalid input/ID, 401 no valid account session, 403 invalid CSRF token, 404 absent/unowned trip, 415 non-JSON body, 503 unavailable database, 500 unexpected failure. Internal exception contents are never returned.

## Person Four authentication handoff

After verifying the password, clear the session and set session["user_id"] = str(user["_id"]). On logout clear the session. Use TRAVELMATE_SECRET_KEY for signing; never accept a user ID from request JSON as authentication. Each route checks that the session account still exists in the users collection.

The factory reads MONGODB_URI and MONGODB_DATABASE (default travelmate) from environment variables. database.init_db exposes current_app.extensions["mongo_db"]. Person Four may inject an existing Database using MONGO_DB when creating the app, or adapt database.get_db to their shared connection. No registration or login endpoints are implemented by Person Three, and there is no production test-login shortcut.

## Person Two frontend handoff

After login call GET /api/csrf-token with the same-origin session cookie. Read csrf_token from the JSON and send it in X-CSRF-Token on POST, PUT and DELETE. Send Content-Type: application/json for POST and PUT. This token is session-specific and refreshed after logout/login. The endpoint returns Cache-Control: no-store. The frontend calls Flask, never MongoDB directly.

## Person Five activities handoff

DELETE currently removes only the owned trip. Agree on activity cleanup before merging activities; this implementation does not claim cascade deletion. Activity routes must verify the parent trip still exists and is owned. Admin routes remain separate and require Person Four's role protection.

## Testing and live demo

Run: .venv\Scripts\python.exe -m unittest discover -s tests -v

Automated tests cover CRUD, repeat reads, owner isolation, unknown/deleted accounts, missing fields, invalid dates/budget/status, malformed JSON, bad IDs, missing resources, CSRF rejection, database error redaction, and the public homepage without MongoDB. The unit tests do not prove live persistence or login integration. A separate live test verifies persistence across application instances.

After Person Four merges auth, use a dedicated development database: log in, obtain CSRF token, POST a trip, GET it, restart Flask and GET it again, PUT changed values, GET again, then DELETE. Log in as a second user and verify the first user's trip is absent from the list and GET/PUT/DELETE return 404. Record the actual results before release. Never run destructive tests against production data.

## Professor question practice

CRUD means Create, Read, Update, Delete. Our methods are POST, GET, PUT, DELETE. create_trip validates JSON, assigns the signed-session owner, calls insert_one and returns 201. list_trips/read_trip query MongoDB and return 200. update_trip uses find_one_and_update with an owner-scoped filter and returns the saved document. delete_trip uses delete_one with the same filter. Both _id and user_id must match for reading, editing or deleting a single trip, so User A cannot access User B's record even if they know its ID. We return 404 in both missing and unowned cases to avoid disclosing other users' data.

The data flow is form -> JavaScript fetch JSON -> Flask blueprint -> session and CSRF checks -> validation -> MongoDB -> JSON response -> frontend. To demonstrate, open the corresponding route function and show the owner filter and MongoDB operation.

## Verification evidence October 7 2026

All eight tests passed on Python 3.13 with Flask 3.1.2 and PyMongo 4.18.2.
The live integration test connected to mongodb://127.0.0.1:27017, created
a uniquely named temporary test database, verified create/read across separate
Flask instances/update/delete, and removed that database afterward.
Actual password login and frontend integration remain pending teammates.

To repeat live tests in PowerShell:

```powershell
$env:TRAVELMATE_TEST_MONGODB_URI = "mongodb://127.0.0.1:27017"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use only a development server with permission to create/drop the uniquely named
test database. If the environment variable is absent, the live test is skipped.
