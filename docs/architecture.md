# Architecture and ownership

Browser HTML/CSS/JavaScript → same-origin fetch/JSON → Flask REST API → MongoDB.
The frontend never connects directly to MongoDB. Flask validates sessions,
ownership, and input before accessing data; returned JSON drives UI updates.

Current files: `app.py` provides `create_app()`, `/`, and the dashboard form
routes; `templates/base.html` provides shared navigation/layout;
`templates/index.html` provides the login/destinations homepage;
`templates/dashboard.html` provides the user dashboard; `static/css/style.css`
provides responsive styling.

## Integration boundaries

- Person 1: factory composition, homepage/navigation integration, final merges.
- Person 2: refine dashboard/forms behavior and any progressive-enhancement
  JavaScript tied to the dashboard UI.
- Person 3: trip/destination API blueprint in `routes/trips.py` and shared trip
  validation rules.
- Person 4: database initialization plus authentication/session policy
  hardening if the team expands beyond the current demo login flow.
- Person 5: activities/admin blueprints, QA coordination, README coordination.

The trip blueprint, seeded-login flow, server-rendered dashboard, and database
adapter now exist. Activities and broader admin workflows remain future team
integrations.
Keep route modules independent of a global Flask app; use blueprints and
`current_app` so tests and clean setups can create separate app instances.

## Person Three implementation

The factory registers `routes/trips.py`. `database.py` supplies `init_db/get_db`
and reads configured MongoDB settings. Authentication currently uses a signed
Flask session set by the homepage login form; API requests recheck the session
user against MongoDB on every request. See
[Person Three notes](person-3-api-notes.md) for configuration and CSRF usage.

## MongoDB data and local setup

The app reads `MONGODB_URI` and `MONGODB_DATABASE` from the process environment;
`app.py` loads `.env` at app creation. Local MongoDB may use
`mongodb://localhost:27017/`; the default database name is `travelmate`. Keep
Atlas credentials in an untracked `.env` or deployment environment.

`database.py` installs the configured database into `app.extensions["mongo_db"]`
and exposes it through `get_db()`. The app uses `users`, `destinations`, and
`trips` collections. User documents include `name`, `email`,
`password_hash`, `active`, and `role`; destinations include `name` and
`price`; trips include MongoDB ObjectIds `user_id` and `destination_id`. Trip
ownership is assigned from the authenticated session and enforced in every trip
query.

`seed_users.py` reads the `users`, `destinations`, and `trips` arrays from root
`data.json`, inserts missing users by email and missing destinations/trips by
`_id`, and resolves trip owners to the actual database user ObjectId. It is
safe to rerun without overwriting existing records. The sample credentials are
for local testing only; the implemented login is a homepage form post rather
than a standalone JSON auth API.
