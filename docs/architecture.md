# Architecture and ownership

Browser HTML/CSS/JavaScript → same-origin `fetch()`/JSON or form posts → Flask
→ MongoDB. The browser never connects to MongoDB or sees its credentials. Flask
checks the session, role, CSRF token, ownership, and input before touching data.

## Files

- `app.py`: `create_app()` factory, homepage login/sign-up (`/`), logout, the
  server-rendered `/dashboard` and `/admin` pages, and their HTML form routes.
- `routes/trips.py`: the `/api` blueprint (destinations, trips, admin users and
  trips), its JSON error handling, the `authenticated`/`require_admin`
  decorators, and helpers shared with `app.py` (`admin_users`, `admin_trips`,
  `trip_schedule`).
- `database.py`: `init_db(app)` and `get_db()`.
- `seed_users.py` + `data.json`: idempotent sample data loader.
- `templates/`: `base.html` layout, `index.html` homepage, `dashboard.html`,
  `admin.html`.
- `static/css/style.css`, `static/js/app.js` (menu, slideshow),
  `static/js/trips.js` (dashboard API calls).

## Request flows

- **Login/sign-up:** form post to `/` → password hash check (or new `user`
  account) → session cleared and refilled → redirect to `/dashboard` or `/admin`.
- **User trip CRUD:** dashboard form → `trips.js` `fetch()` with JSON and
  `X-CSRF-Token` → `/api/trips` → owner-scoped MongoDB query → JSON → card list
  re-rendered. Without JavaScript the form posts to `/dashboard/trips...` and
  the page reloads.
- **Admin:** `/admin` page forms post to `/admin/...` routes; the same data is
  available as JSON from `/api/admin/users`, `/api/admin/trips`, and
  `/api/destinations`.

## Integration boundaries

- Person 1: factory composition, homepage/navigation integration, final merges.
- Person 2: dashboard/forms behavior and the `trips.js` progressive enhancement.
- Person 3: trip/destination API blueprint in `routes/trips.py` and shared
  validation rules.
- Person 4: database initialization plus authentication/session policy.
- Person 5: admin features, QA coordination, README coordination.

Trip activities were scoped out; trips, destinations, and admin management
cover the assignment requirements. Keep route modules independent of a global
Flask app; use blueprints and `current_app` so tests and clean setups can
create separate app instances.

## Authentication

Authentication uses a signed Flask session set by the homepage form. Every
protected page and API request reloads the session user from MongoDB, so deleted accounts
lose access immediately. Admin access is checked server-side from the stored
`role`, never from anything the browser sends. See
[Person Three notes](person-3-api-notes.md) for CSRF usage.

## MongoDB data and local setup

The app reads `MONGODB_URI` and `MONGODB_DATABASE` from the environment;
`app.py` loads `.env` at app creation. Local development uses the
`travelmate-mongo` Docker container at `mongodb://127.0.0.1:27017` (see the
README); the default database name is `travelmate`. Keep Atlas credentials in
an untracked `.env` or deployment environment.

`database.py` installs the configured database into `app.extensions["mongo_db"]`
and exposes it through `get_db()`; tests inject an in-memory double through
`MONGO_DB`. Collections:

- `users`: `name`, `email`, `password_hash`, `active`, `role`
- `destinations`: `name`, `price`
- `trips`: ObjectIds `user_id` and `destination_id`, plus `title`,
  `start_date`, `end_date`, `budget`, `description`, `status`

Trip ownership is assigned from the authenticated session and enforced in every
user trip query. A destination cannot be deleted while a trip references it.

`seed_users.py` reads the `users`, `destinations`, and `trips` arrays from
`data.json`, inserts missing users by email and missing destinations/trips by
`_id`, and resolves trip owners to the real database user ObjectId. It is safe
to rerun and never overwrites existing records.
