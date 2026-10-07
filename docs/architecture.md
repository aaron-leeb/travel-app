# Architecture and ownership

Browser HTML/CSS/JavaScript → same-origin fetch/JSON → Flask REST API → MongoDB.
The frontend never connects directly to MongoDB. Flask validates sessions,
ownership, and input before accessing data; returned JSON drives UI updates.

Current files: `app.py` provides `create_app()` and `/`; `templates/base.html`
provides shared navigation/layout; `templates/index.html` provides the public
homepage; `static/css/style.css` provides responsive styling.

## Integration boundaries

- Person 1: factory composition, homepage/navigation integration, final merges.
- Person 2: dashboard/forms and JavaScript fetch; coordinate changes to shared
  CSS/base layout with Person 1. Suggested files: `templates/dashboard.html`,
  `static/js/trips.js`.
- Person 3: trip API blueprint in `routes/trips.py`; Person 1 registers it in
  the factory when available. API must depend on Person 4's verified identity
  helper rather than a client-supplied user ID.
- Person 4: database initialization, authentication blueprint, session identity
  and role helpers. Agree on helper signatures with Person 3 before CRUD work.
- Person 5: activities/admin blueprints, QA coordination, README coordination.

The trip blueprint and database adapter now exist; authentication, dashboard,
and activities/admin remain teammate integrations.
Keep route modules independent of a global Flask app; use blueprints and
`current_app` so tests and clean setups can create separate app instances.

## Decisions needing team confirmation

Person 2's Monday homepage task overlaps Person 1 ownership: this foundation
implements it; Person 2 should coordinate polish rather than duplicate it.
MongoDB hosting, configuration names, auth helper signatures, admin provisioning,
and activities release scope remain open. Use one origin for pages and API by
default to avoid unnecessary CORS and cross-origin session configuration.

## Person Three implementation

The factory registers routes/trips.py. database.py supplies init_db/get_db and
reads configured MongoDB settings. The verified-login handoff is a signed
session user_id, checked against users on every request; see
[Person Three notes](person-3-api-notes.md) for configuration and CSRF usage.
