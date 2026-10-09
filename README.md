# TravelMate (CS 485 Final Project)

## Team Members
Abel Mechal
Betlehem Gebremeskel
Aaron Leeb
Jabali Muriithi
Zaina Nadeem

## Project Description
TravelMate is a full-stack travel planning web application. Users register, log
in, and create, edit, and delete trips to destinations offered by the site;
their trips persist across sessions. Administrators have a separate, protected
dashboard for managing destinations and viewing every user and trip. The
project is intentionally scoped to demonstrate the core CS 485 requirements
reliably within a five-day development window; trip activities were considered
and deliberately left out of scope.

## Project Goals
 - Provide a clear travel-planning use case with a simple, demo-friendly workflow.
 - Demonstrate responsive frontend development with HTML, CSS, and JavaScript.
 - Implement a REST API using GET, POST, PUT, and DELETE with JSON requests/responses.
 - Persist application data in MongoDB so information remains after page refresh.
 - Implement secure authentication with password hashing, sessions, logout, and two roles: User and Admin.
 - Demonstrate complete full-stack integration and role-protected functionality.

## Features

**Everyone (homepage `/`)**
- Log in or sign up from the hero form. Sign-up always creates a normal user.
- Browse the available destinations and their starting prices.

**Users (`/dashboard`)**
- See all of their own trips as itinerary cards (dates, nights, budget, status, notes).
- Plan a new trip from the list of available destinations.
- Edit a trip's title, dates, budget, status, and notes; delete a trip.
- These actions call the JSON API with `fetch()`, so the page updates without
  reloading. The same forms also work as plain HTML posts if JavaScript is off.

**Admins (`/admin`)**
- Add destinations, change destination prices, and delete destinations that no
  trip uses.
- See every user account (name, email, role, active state).
- See every trip with its owner and delete any trip.

**Security**
- Passwords are stored as Werkzeug scrypt hashes; hashes are never returned.
- Signed Flask session cookies (`HttpOnly`, `SameSite=Lax`); logout clears the session.
- CSRF token on every write (hidden form field, or `X-CSRF-Token` header for the API).
- Server-side role checks on every admin page and API route; users can only
  read or change their own trips (other users' trips return 404).

## Running locally (Windows / PowerShell)

Requirements: Python 3.12 or newer (developed on 3.13) and Docker Desktop (or
any MongoDB 7 server).

Run everything from the repository root.

**1. Start MongoDB.** First time only, create the container:

```powershell
docker run -d --name travelmate-mongo -p 27017:27017 -v travelmate-mongo-data:/data/db mongo:7
```

After that, just start it (for example after a reboot):

```powershell
docker start travelmate-mongo
```

If you installed MongoDB Community Server instead, make sure the `MongoDB`
Windows service is running; `mongosh` is only a client and does not start a
server.

**2. Create the virtual environment and install dependencies** (first time only):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**3. Create `.env`** (first time only), then edit `TRAVELMATE_SECRET_KEY` to a
private random value:

```powershell
Copy-Item example.env .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

**4. Seed the sample data** (safe to rerun; it never overwrites existing records):

```powershell
.\.venv\Scripts\python.exe seed_users.py
```

**5. Run the app** and open http://127.0.0.1:5000:

```powershell
.\.venv\Scripts\python.exe -m flask --app app:create_app run
```

Stop it with Ctrl+C. Flask does not reload templates on its own; restart it
after changing Python or template files (or add `--debug` while developing).

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python` in place of
`.\.venv\Scripts\python.exe`.

### Demo accounts

Created by `seed_users.py`, for local testing only:

- User: `user@example.com` / `testuser`
- Admin: `admin@example.com` / `testadmin`

## Configuration

`.env` (copied from `example.env`, never committed):

| Variable | Purpose | Default |
| --- | --- | --- |
| `MONGODB_URI` | MongoDB connection string. Use your private Atlas URI if not running locally. | none (database features return 503) |
| `MONGODB_DATABASE` | Database name | `travelmate` |
| `TRAVELMATE_SECRET_KEY` | Signs session cookies | a fixed local-development key |

The homepage still renders without MongoDB, but login, the dashboards, and the
API need a running, seeded database.

## Data model

MongoDB collections:

- `users`: `name`, `email`, `password_hash`, `active`, `role` (`user` or `admin`)
- `destinations`: `name`, `price`
- `trips`: `user_id` and `destination_id` (ObjectId references), `title`,
  `start_date`, `end_date` (YYYY-MM-DD), `budget`, `description`, `status`
  (`Planned`, `Ongoing`, or `Completed`)

Sample records live in `data.json`.

## Project structure

```
app.py               App factory, login/sign-up, dashboard and admin page routes
routes/trips.py      JSON API blueprint (/api/...) and shared admin/schedule helpers
database.py          MongoDB connection (init_db / get_db)
seed_users.py        Loads data.json into MongoDB
templates/           base, index (homepage), dashboard, admin
static/css/style.css All styling (Jost font, peach/copper theme)
static/js/app.js     Mobile menu and homepage hero slideshow
static/js/trips.js   Dashboard fetch() calls to the trips API
tests/               Unit tests (in-memory database) and live MongoDB tests
docs/                API contract, architecture, checklists, presentation notes
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The unit tests use an in-memory database and need nothing running. Two live
tests also run against real MongoDB when `TRAVELMATE_TEST_MONGODB_URI` is set;
each creates and then drops its own uniquely named temporary database:

```powershell
$env:TRAVELMATE_TEST_MONGODB_URI = "mongodb://127.0.0.1:27017"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Team references

- [API contract](docs/api-contract.md)
- [Architecture and ownership](docs/architecture.md)
- [API implementation notes and professor question practice](docs/person-3-api-notes.md)
- [Integration/release checklist](docs/integration-checklist.md)
- [Presentation notes](docs/presentation-notes.md)
- [Git and integration workflow](docs/workflow.md)
- [Frontend notes](FRONTEND_README.md) and [photo guide](PHOTO_GUIDE.md)
