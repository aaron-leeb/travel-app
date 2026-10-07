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
implemented. Authentication, MongoDB, dashboard, trip CRUD, and admin/activity
features are not implemented yet. The homepage example is illustrative data.

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
a hardcoded fallback; never commit it. MongoDB configuration will be documented
when Person 4 supplies the connection implementation. Flask's development
server is for development only.

## Team references

- [Architecture and ownership](docs/architecture.md)
- [Proposed API contract](docs/api-contract.md)
- [Git and integration workflow](docs/workflow.md)
- [Integration/release checklist](docs/integration-checklist.md)
- [Person 1 presentation notes](docs/presentation-notes.md)
