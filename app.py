"""TravelMate application factory and public page routes."""

import os

from flask import Flask, render_template

from database import init_db
from routes.trips import bp as trips_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("TRAVELMATE_SECRET_KEY"),
        MONGODB_URI=os.environ.get("MONGODB_URI"),
        MONGODB_DATABASE=os.environ.get("MONGODB_DATABASE", "travelmate"),
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config is not None:
        app.config.update(test_config)

    init_db(app)
    app.register_blueprint(trips_bp)

    # Register teammates' authentication/activity blueprints when merged.
    @app.get("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
