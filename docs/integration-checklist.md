# Integration and release checklist

Unchecked items are not validated or implemented merely by being listed. Ticks
below were verified on October 8 2026 with the full test suite (21 passing,
including live MongoDB tests) and manual browser checks.

## Foundation

- [x] Flask factory serves homepage and stylesheet.
- [x] Navigation targets existing homepage sections.
- [x] Homepage login renders and user sessions redirect to the dashboard.
- [ ] All five members verify local startup using the README.
- [ ] Person 4 verifies MongoDB connection and configuration.
- [ ] Persons 2/3/4 confirm API contract and auth interfaces.
- [ ] Verify layout/keyboard behavior in a browser at mobile/tablet/desktop
  widths. (Desktop and ~870px checked; phone width and keyboard-only not yet.)

## Required end-to-end gate

- [x] Login; incorrect password fails; authenticated dashboard opens.
- [ ] Create a trip through UI; inspect saved database record in MongoDB
  (UI create and API read verified; direct database inspection not yet done).
- [x] Read trip/list; refresh and confirm persistence.
- [x] Update and refresh; delete and confirm removal from UI.
- [x] Two users: User A cannot read/update/delete User B's trip via direct API.
- [x] Test malformed input, invalid IDs, missing fields, nonexistent records.
- [x] Logout route implemented; protected pages and API reject subsequent access.
- [x] Normal user denied direct admin API requests.
- [x] Admin lists users/trips and deletes a trip; no hashes exposed.
- [x] Session write protection (CSRF on every form and API write).
- [ ] Each machine sets a private `TRAVELMATE_SECRET_KEY` in `.env` (the
  `example.env` placeholder must be replaced).

## Scope and release

- [x] Activities decision: out of scope. Deleting a trip removes only the trip.
- [ ] Record each owner's normal/failure tests and post-merge results.
- [ ] Audit rubric and obtain each owner's sign-off.
- [ ] Clean copy installs/runs using README without undocumented steps.
- [ ] Complete full demo and instructor-question rehearsal.
- [ ] Final ZIP excludes `.venv`, `.git`, `.env`, `__pycache__`, `.DS_Store`,
  and unused images.
- [ ] Extract ZIP and rerun setup/demo; verify source and slides are included.

Current status: all required features are implemented: sign-up/login/logout,
user trip CRUD through the JSON API, admin destination management, and admin
user/trip oversight. Remaining work is team verification, presentation
rehearsal, and packaging.
