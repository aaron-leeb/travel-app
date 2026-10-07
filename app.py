"""TravelMate application factory and public page routes."""

import os

from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("TRAVELMATE_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config is not None:
        app.config.update(test_config)

    destinations = [
        ("Venice", "venice", 199, "Wander along canals and discover the charm of Italy."),
        ("San Pedro", "beach", 249, "Slow down by palm-lined beaches and turquoise water."),
        ("Barbados", "marina", 299, "Enjoy island life, ocean views, and sunny adventures."),
        ("Cyprus", "cyprus", 239, "Explore colorful streets and a beautiful Mediterranean coast."),
    ]

    home_destinations = [
        ("Sahara, Morocco", "desert", 349, "Warm · Golden dunes and nights beneath the stars."),
        ("San Pedro", "beach", 249, "Warm · Palm-lined beaches and turquoise water."),
        ("Barbados", "marina", 299, "Warm · Island life and sunny adventures."),
        ("Cyprus", "cyprus", 239, "Warm · Mediterranean coast and colorful streets."),
        ("Swiss Alps", "alpine", 399, "Cold · Snowy peaks and cozy mountain villages."),
        ("Iceland", "alpine", 449, "Cold · Glaciers and winter landscapes."),
        ("Norway", "alpine", 429, "Cold · Nordic scenery and snowy adventures."),
        ("Banff, Canada", "alpine", 379, "Cold · Mountain lakes and alpine trails."),
    ]

    @app.get("/packages")
    @app.get("/tours")
    @app.get("/about")
    @app.get("/contact")
    def public_page():
        from flask import request
        page = request.path.strip("/")
        titles = {"packages": "Vacation Packages", "tours": "Unforgettable Tours", "about": "About TravelMate", "contact": "Get In Touch"}
        return render_template("page.html", page=page, title=titles[page],
            subtitle="Explore the World with us.", heading="Discover Your Next Getaway", destinations=destinations)

    # Register teammates' blueprints here once their implementations are merged.
    @app.get("/")
    def index():
        return render_template("index.html", destinations=home_destinations)

    return app
