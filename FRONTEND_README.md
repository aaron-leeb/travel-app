# TravelMate frontend

Run from this folder:

```sh
python -m pip install -r requirements.txt
python -m flask --app app:create_app run --debug
```

Open http://127.0.0.1:5000. Pages: /, /packages, /tours, /about, /contact.

Frontend files are in templates/, static/css/style.css, static/js/app.js, and static/images/. The small additions to app.py register the public pages.

The layout follows the provided reference with a coastal hero, teal search tabs, destination cards, a scenic banner, features, gallery, newsletter, and footer. Photos were extracted from the supplied reference and can be replaced with higher-resolution licensed originals using the same filenames.

Search, subscriptions, contact, and trip details are explicitly frontend demonstrations. Connect them to your teammates' backend routes before using them for real submissions or bookings. No data is sent or retained.

## Sahara theme update
The existing page layout is preserved. Peach and sand backgrounds, copper buttons, warm brown text, bold white hero headings, and a desert photo treatment follow the new reference. Destination photos stay in the destination cards. The desert asset is a low-resolution text-free crop from the supplied screenshot; replace static/images/desert.jpg with a high-resolution desert photo for sharper results.
