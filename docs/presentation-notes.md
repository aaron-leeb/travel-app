# Person 1 presentation notes

Slides: 1 title/team; 2 problem/intended users; 3 solution/core features;
4 live demo; 5 architecture/data flow.

TravelMate helps travelers organize trips: destination, dates, budget, status,
and notes. Users see only their own trips; admins have a separately protected
dashboard for destinations, every user, and every trip. Explain only completed
behavior as working in the final demo.

Scope note, if asked: trip activities were considered and deliberately cut so
the required features (auth, roles, REST CRUD, persistence) could be finished
and tested properly within the five-day window.

Trace the Create Trip flow: dashboard form → `trips.js` `fetch()` with JSON and
the CSRF header → `POST /api/trips` in `routes/trips.py` → session user
reloaded from MongoDB → input validation → `insert_one` with the session user
as owner → 201 JSON → `trips.js` reloads the list and re-renders the cards.
Refresh proves persistence. Browser DevTools → Network shows each request.

Show exact files/functions, explain how PRs and post-merge checks protect the
shared application, and explain why the browser never receives database
credentials or talks directly to MongoDB.

Demo order: homepage, sign up a new user, log out, log in as the demo user,
create/read/refresh/edit/delete a trip, try another user's trip ID via the API
(404), logout, admin login, destination add/price edit, user and trip lists,
admin deletes a trip, normal-user admin denial, architecture recap.

Person 3 explains CRUD routes; Person 4 explains auth/database; Person 2 explains
UI/fetch; Person 5 explains admin/test evidence. Rehearse without handing off
questions about your own responsibilities.
