# Travel-Mate (CS 485 Final Project)
## Team Members
Abel Mechal
Betlehem Gebremeskel
Aaron Leeb
Jabali Muriithi
Zaina Nadeem

## Project Description
TravelMate is a full-stack travel planning web application that allows users to register, log in, create and manage trips, add travel activities, and view their saved information across sessions. The system also includes an administrator role with protected access to system-wide user and trip information. The project is intentionally scoped to demonstrate the core CS 485 requirements reliably within a five-day development window rather than adding high-risk optional features.

## Project Goals
 - Provide a clear travel-planning use case with a simple, demo-friendly workflow.
 - Demonstrate responsive frontend development with HTML, CSS, and JavaScript.
 - Implement a REST API using GET, POST, PUT/PATCH, and DELETE with JSON requests/responses.
 - Persist application data in MongoDB so information remains after page refresh.
 - Implement secure authentication with password hashing, sessions, logout, and two roles: User and Admin.
 - Demonstrate complete full-stack integration and role-protected functionality.


## Development setup and integration


CS 485 travel-planning project. Users will manage personal trips; administrators
will have protected access to system-wide information.

## Current implementation

The Flask application factory, responsive public homepage, and navigation are
implemented. Trip CRUD APIs, a MongoDB adapter, validation, ownership checks, and CSRF
protection are implemented. Authentication, dashboard, and admin/activity
features still require teammate integration. The homepage example is illustrative data.

## Local setup

Use Python 3.12 (the foundation was verified with 3.12.14).
From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app:create_app run --host 127.0.0.1 --port 5000
```

Open the server in your local browser. No database or credentials are needed for
the current public homepage. Stop the development server with Ctrl+C.

Before authentication is integrated, set `TRAVELMATE_SECRET_KEY` to a securely
generated private value in your local environment. The factory reads it without
a hardcoded fallback; never commit it. Set MONGODB_URI and MONGODB_DATABASE for trip persistence. The database adapter
is available for Person 4 to reuse with authentication. Flask's development
server is for development only.

## Team references

- [Architecture and ownership](docs/architecture.md)
- [Proposed API contract](docs/api-contract.md)
- [Git and integration workflow](docs/workflow.md)
- [Integration/release checklist](docs/integration-checklist.md)
- [Person 1 presentation notes](docs/presentation-notes.md)

## Person Three API setup on Windows

From the cloned travel-app folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:MONGODB_URI = "mongodb://127.0.0.1:27017"
$env:MONGODB_DATABASE = "travelmate"
$env:TRAVELMATE_SECRET_KEY = (.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))")
.\.venv\Scripts\python.exe -m flask --app app:create_app run
```

Use your team's MongoDB URI instead of localhost if using Atlas. Keep it private.
example.env is a reference; .env files are not loaded automatically. Public
homepage works without MongoDB. Protected APIs require Person Four's login
implementation; no login endpoint exists yet.

Run isolated API tests: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
See [Person Three implementation and handoff notes](docs/person-3-api-notes.md)
for JSON, CSRF, authentication integration, and presentation practice.
