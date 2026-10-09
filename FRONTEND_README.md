# TravelMate frontend

Run from this folder:

```sh
python -m pip install -r requirements.txt
python -m flask --app app:create_app run --debug
```

Open http://127.0.0.1:5000. The main page provides demo login/sign-up and shows the available destinations.

Frontend files are in templates/, static/css/style.css, static/js/app.js, and static/images/. The small additions to app.py register the login page, user dashboard, and API integration points.

The layout follows the provided reference with a coastal hero, teal search tabs, destination cards, a scenic banner, features, gallery, newsletter, and footer. Photos were extracted from the supplied reference and can be replaced with higher-resolution licensed originals using the same filenames.

The homepage explains the seeded demo login and current destination list. New accounts can be created from the same homepage with the Sign up button and are always normal user accounts. User logins are redirected to a dashboard for viewing trips and creating new ones from the available destinations. Admin logins are redirected to a separate admin page for adding destinations, updating destination prices, and deleting unused destinations.

## Sahara theme update
The existing page layout is preserved. Peach and sand backgrounds, copper buttons, warm brown text, bold white hero headings, and a desert photo treatment follow the new reference. Destination photos stay in the destination cards. The desert asset is a low-resolution text-free crop from the supplied screenshot; replace static/images/desert.jpg with a high-resolution desert photo for sharper results.
