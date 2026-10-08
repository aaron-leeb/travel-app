# TravelMate frontend

Run from this folder:

```sh
python -m pip install -r requirements.txt
python -m flask --app app:create_app run --debug
```

Open http://127.0.0.1:5000. The main page provides demo login and shows the available destinations.

Frontend files are in templates/, static/css/style.css, static/js/app.js, and static/images/. The small additions to app.py register the login page, user dashboard, and API integration points.

The layout follows the provided reference with a coastal hero, teal search tabs, destination cards, a scenic banner, features, gallery, newsletter, and footer. Photos were extracted from the supplied reference and can be replaced with higher-resolution licensed originals using the same filenames.

The homepage explains the seeded demo login and current destination list. User logins are redirected to a dashboard for viewing trips and creating new ones from the available destinations. Destination creation is handled through the admin API rather than through a separate page.

## Sahara theme update
The existing page layout is preserved. Peach and sand backgrounds, copper buttons, warm brown text, bold white hero headings, and a desert photo treatment follow the new reference. Destination photos stay in the destination cards. The desert asset is a low-resolution text-free crop from the supplied screenshot; replace static/images/desert.jpg with a high-resolution desert photo for sharper results.
