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

The Flask application factory, main-page login/sign-up, user dashboard, admin
destination management page, and trips API are implemented. The homepage signs
in against the seeded `users` collection, allows new normal-user accounts to be
created from the sign-up button, and shows the available destinations. User
logins are redirected to a dashboard where they can review trips and add new
ones from the seeded destination list. Trips now reference seeded
destinations from `data.json` rather than accepting freeform destination text.
Admin users are redirected to a protected `/admin` page where they can add
destinations, update destination prices, and delete destinations that are not
currently referenced by trips. Trip CRUD APIs, a MongoDB adapter, validation,
ownership checks, and CSRF protection are implemented.

## Local setup

Use Python 3.12 (the foundation was verified with 3.12.14).
From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app:create_app run --host 127.0.0.1 --port 5000
```

Open the server in your local browser. The homepage loads without MongoDB, but
login and the trips API require MongoDB plus seeded sample data. Stop the
development server with Ctrl+C.

Copy `example.env` to `.env` and set its values for local development. The app
loads `.env` when creating the Flask app; do not commit secrets. Set
`TRAVELMATE_SECRET_KEY` to a securely generated private value and configure
`MONGODB_URI` and `MONGODB_DATABASE` for trip persistence. Local MongoDB can use
`mongodb://localhost:27017/`; use your private Atlas URI when running against
Atlas. The default database name is `travelmate`. If no secret key is set, the
app falls back to a local-development secret so login/session flows still work,
but you should still set your own private secret in `.env`.

The database uses `users`, `destinations`, and `trips` collections. Trips store
an ObjectId `user_id` referencing the owning user and an ObjectId
`destination_id` referencing an available destination. The API sets ownership
from the session and filters trip operations by that owner. MongoDB is not
needed for the public homepage, but it must be running and configured for
database-backed operations. Flask's development server is for development only.

To add the sample user accounts, destinations, and trip from `data.json` to the
configured database, run `.\.venv\Scripts\python.exe seed_users.py` from the
repository root. The script inserts only users that do not already exist by
email plus destinations/trips that do not already exist by `_id`; it does not
overwrite existing records. Trip ownership is resolved to the user's actual
database `_id`.
The sample credentials are for local testing only:

- `user@example.com` / `testuser`
- `admin@example.com` / `testadmin`

The homepage login uses those seeded accounts. The homepage sign-up button
creates only normal user accounts; it does not create admin users. After login:

- user sessions land on `/dashboard`, where they can review trips and add new
  trips from the available destination list
- admin sessions land on `/admin`, where they can add destinations, edit
  destination prices, and delete destinations that are not in use
- `GET /api/destinations` lists available destinations
- `POST /api/destinations` creates a destination for admin sessions
- trip create/update requests must send `destination_id` for an existing
  destination

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
`example.env` is a reference to copy to `.env`. The homepage renders without
MongoDB, but demo login and protected trip APIs require a configured database
plus `seed_users.py`.

Run isolated API tests: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
To run the opt-in live MongoDB seed check safely against a temporary database:

```powershell
$env:TRAVELMATE_TEST_MONGODB_URI = "mongodb://localhost:27017/"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_seed_users_integration.py -v
```

The test drops only its uniquely named temporary database when it finishes.
See [Person Three implementation and handoff notes](docs/person-3-api-notes.md)
for JSON, CSRF, authentication integration, and presentation practice.
