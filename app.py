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

    # Register teammates' blueprints here once their implementations are merged.
    @app.get("/")
    def index():
        return render_template("index.html")

    return app
