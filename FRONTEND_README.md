# TravelMate frontend

See the [README](README.md) for setup. Once the app is running, open
http://127.0.0.1:5000.

## Files

- `templates/base.html`: shared layout, header (hidden on `/admin`), footer, font and script loading.
- `templates/index.html`: homepage hero slideshow, login/sign-up form, available destinations.
- `templates/dashboard.html`: user planner (trip cards plus the "Plan a trip" form).
- `templates/admin.html`: admin destination management, user list, and all-trips list.
- `static/css/style.css`: all styling.
- `static/js/app.js`: mobile menu toggle and the homepage slideshow.
- `static/js/trips.js`: dashboard create/edit/delete through `fetch()` and the JSON API.
- `static/images/`: slideshow photos (see [PHOTO_GUIDE.md](PHOTO_GUIDE.md)).

## Design

- Theme: peach and sand backgrounds, copper buttons, warm brown text. Colours
  are CSS variables at the top of `style.css` (`--ink`, `--copper`, `--paper`, ...).
- Font: [Jost](https://fonts.google.com/specimen/Jost) from Google Fonts, with
  light weights for large headings and small spaced uppercase for labels. The
  `--font` variable has system fallbacks if Google Fonts is unreachable.
- Dashboard: trips are itinerary cards with a date block (month/day), destination,
  date range, nights, budget, status pill, and notes. "Edit trip" expands an
  inline form. On wide screens the "Plan a trip" card sits on the right and
  stays in view while scrolling; under 900px it stacks above the trip list.
- Admin: an add-destination bar styled like the homepage login bar, destination
  cards two per row with inline price editing, and row lists for users and trips.

## Dashboard JavaScript

`trips.js` intercepts the dashboard forms and calls the API instead:

| Action | Request |
| --- | --- |
| Plan a trip | `POST /api/trips` |
| Save changes | `PUT /api/trips/<id>` |
| Delete | `DELETE /api/trips/<id>` |

Each call sends JSON with the page's CSRF token in the `X-CSRF-Token` header,
then reloads the list with `GET /api/trips` and shows a status message (or the
API's error message). The card markup in `tripCard()` must stay in sync with
the trip card in `dashboard.html`. Without JavaScript the same forms post to
the `/dashboard/trips...` routes and the page reloads.
