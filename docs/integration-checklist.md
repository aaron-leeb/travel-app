# Integration and release checklist

Unchecked items are not validated or implemented merely by being listed.

## Foundation

- [x] Flask factory serves homepage and stylesheet.
- [x] Navigation targets existing homepage sections.
- [ ] All five members verify local startup.
- [ ] Person 4 verifies MongoDB connection and configuration.
- [ ] Persons 2/3/4 confirm API contract and auth interfaces.
- [ ] Verify layout/keyboard behavior in a browser at mobile/tablet/desktop widths.

## Required end-to-end gate

- [ ] Register; duplicate registration fails clearly; password stored as hash.
- [ ] Login; incorrect password fails; authenticated dashboard opens.
- [ ] Create a trip through UI; inspect saved database record.
- [ ] Read trip/list; refresh and confirm persistence.
- [ ] Update and refresh; delete and confirm removal from database/UI.
- [ ] Two users: User A cannot read/update/delete User B's trip via direct API.
- [ ] Test malformed input, invalid IDs, missing fields, nonexistent records.
- [ ] Logout; protected pages and API reject subsequent access.
- [ ] Normal user denied admin page and direct admin API requests.
- [ ] Admin lists users/trips and deletes a trip; no hashes exposed.
- [ ] Confirm session write protection and secret configuration.

## Activities and release

- [ ] Agree whether activities are committed scope; document trip-delete policy.
- [ ] If included: add/list/delete activities, refresh, and test ownership.
- [ ] Record each owner's normal/failure tests and post-merge results.
- [ ] Audit rubric and obtain each owner's sign-off.
- [ ] Clean copy installs/runs using README without undocumented steps.
- [ ] Complete full demo and instructor-question rehearsal.
- [ ] Final ZIP excludes `.venv`, `.git`, credentials, and generated clutter.
- [ ] Extract ZIP and rerun setup/demo; verify source and slides are included.

Current blockers: no MongoDB/authentication, trip API/dashboard, admin, or
activities implementation exists. Final merges/release cannot be claimed until
those owner contributions are available. Instructor deadline remains unverified.
