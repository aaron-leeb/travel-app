"""TravelMate application factory, login, and user dashboard."""

import os
import math
import secrets
from datetime import date

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, current_app, redirect, render_template, request, session, url_for
from pymongo.errors import PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_db
from routes.trips import admin_trips, admin_users, bp as trips_bp, trip_schedule

DEFAULT_DEV_SECRET_KEY = "travelmate-local-dev-secret-key"


def authenticate_user(email, password):
    user = get_db().users.find_one({"email": email.strip().lower()})
    if user is None or not user.get("active"):
        return None

    password_hash = user.get("password_hash")
    if not isinstance(password_hash, str) or not check_password_hash(password_hash, password):
        return None

    return user


def validated_signup_credentials():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return None, None, "Enter both email and password."
    if len(email) > 320 or "@" not in email or email.startswith("@") or email.endswith("@"):
        return None, None, "Enter a valid email address."
    if len(password) < 8:
        return None, None, "Password must be at least 8 characters."
    return email, password, None


def login_credentials():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        return None, None, "Enter both email and password."
    return email, password, None


def create_user_account(email, password):
    existing_user = get_db().users.find_one({"email": email})
    if existing_user is not None:
        return None, "An account with that email already exists."
    new_user = {
        "email": email,
        "name": email,
        "password_hash": generate_password_hash(password),
        "active": True,
        "role": "user",
    }
    inserted = get_db().users.insert_one(new_user)
    new_user["_id"] = inserted.inserted_id
    return new_user, None


def current_user():
    user_id = session.get("user_id")
    if not isinstance(user_id, str) or not ObjectId.is_valid(user_id):
        return None
    return get_db().users.find_one({"_id": ObjectId(user_id)})


def store_session_user(user):
    session["user_id"] = str(user["_id"])
    session["user_name"] = user.get("name") or user["email"]
    session["user_role"] = user.get("role", "user")
    session["user_email"] = user["email"]


def ensure_csrf_token():
    if not isinstance(session.get("csrf_token"), str):
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf():
    expected = session.get("csrf_token")
    supplied = request.form.get("csrf_token", "")
    if not isinstance(expected, str) or not secrets.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8")):
        return "Refresh the page and try again."
    return None


def destination_cards():
    destinations = get_db().destinations.find({}).sort("name", 1)
    return [{"name": destination["name"], "price": destination["price"]} for destination in destinations]


def is_admin(user):
    return user is not None and user.get("role") == "admin"


def user_trip_cards(user_id):
    destinations = {
        destination["_id"]: destination
        for destination in get_db().destinations.find({})
    }
    trips = get_db().trips.find({"user_id": user_id}).sort("_id", -1)
    result = []
    for trip in trips:
        destination = destinations.get(trip.get("destination_id"))
        if destination is None:
            continue
        result.append(
            {
                "_id": str(trip["_id"]),
                "title": trip["title"],
                "destination_id": str(destination["_id"]),
                "destination": destination["name"],
                "start_date": trip["start_date"],
                "end_date": trip["end_date"],
                "budget": trip["budget"],
                "description": trip.get("description", ""),
                "status": trip["status"],
                **trip_schedule(trip["start_date"], trip["end_date"]),
            }
        )
    return result


def dashboard_form_destinations():
    destinations = get_db().destinations.find({}).sort("name", 1)
    return [{"_id": str(destination["_id"]), "name": destination["name"], "price": destination["price"]} for destination in destinations]


def admin_destinations():
    destinations = get_db().destinations.find({}).sort("name", 1)
    result = []
    for destination in destinations:
        result.append(
            {
                "_id": str(destination["_id"]),
                "name": destination["name"],
                "price": destination["price"],
            }
        )
    return result


def validated_trip_form():
    title = request.form.get("title", "").strip()
    if not title or len(title) > 200:
        return None, "Title is required and must be 200 characters or fewer."

    destination_id = request.form.get("destination_id", "")
    if not ObjectId.is_valid(destination_id):
        return None, "Choose an available destination."
    destination = get_db().destinations.find_one({"_id": ObjectId(destination_id)})
    if destination is None:
        return None, "Choose an available destination."

    trip = {
        "title": title,
        "destination_id": destination["_id"],
        "description": request.form.get("description", "").strip(),
    }
    if len(trip["description"]) > 5000:
        return None, "Description must be 5000 characters or fewer."

    for field in ["start_date", "end_date"]:
        value = request.form.get(field, "")
        try:
            if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError:
            return None, f"{field.replace('_', ' ').title()} must be a valid date."
        trip[field] = value
    if trip["end_date"] < trip["start_date"]:
        return None, "End date must be on or after start date."

    budget_text = request.form.get("budget", "")
    try:
        budget = float(budget_text)
        valid_budget = math.isfinite(budget) and budget >= 0
    except ValueError:
        valid_budget = False
        budget = None
    if not valid_budget:
        return None, "Budget must be a finite nonnegative number."
    trip["budget"] = int(budget) if budget.is_integer() else budget

    status = request.form.get("status", "Planned")
    if status not in {"Planned", "Ongoing", "Completed"}:
        return None, "Status must be Planned, Ongoing, or Completed."
    trip["status"] = status
    return trip, None


def owned_dashboard_trip(user_id, trip_id):
    if not ObjectId.is_valid(trip_id):
        return None
    return get_db().trips.find_one({"_id": ObjectId(trip_id), "user_id": user_id})


def validated_trip_edit_form(existing_trip):
    title = request.form.get("title", "").strip()
    if not title or len(title) > 200:
        return None, "Title is required and must be 200 characters or fewer."

    trip = {
        "title": title,
        "destination_id": existing_trip["destination_id"],
        "description": request.form.get("description", "").strip(),
    }
    if len(trip["description"]) > 5000:
        return None, "Description must be 5000 characters or fewer."

    for field in ["start_date", "end_date"]:
        value = request.form.get(field, "")
        try:
            if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError:
            return None, f"{field.replace('_', ' ').title()} must be a valid date."
        trip[field] = value
    if trip["end_date"] < trip["start_date"]:
        return None, "End date must be on or after start date."

    budget_text = request.form.get("budget", "")
    try:
        budget = float(budget_text)
        valid_budget = math.isfinite(budget) and budget >= 0
    except ValueError:
        valid_budget = False
        budget = None
    if not valid_budget:
        return None, "Budget must be a finite nonnegative number."
    trip["budget"] = int(budget) if budget.is_integer() else budget

    status = request.form.get("status", "Planned")
    if status not in {"Planned", "Ongoing", "Completed"}:
        return None, "Status must be Planned, Ongoing, or Completed."
    trip["status"] = status
    return trip, None


def validated_destination_form():
    name = request.form.get("name", "").strip()
    if not name or len(name) > 200:
        return None, "Destination name is required and must be 200 characters or fewer."
    for existing in get_db().destinations.find({}):
        if existing.get("name", "").strip().casefold() == name.casefold():
            return None, "A destination with that name already exists."

    price_text = request.form.get("price", "")
    try:
        price = float(price_text)
        valid_price = math.isfinite(price) and price >= 0
    except ValueError:
        valid_price = False
        price = None
    if not valid_price:
        return None, "Price must be a finite nonnegative number."
    return {"name": name, "price": int(price) if price.is_integer() else price}, None


def validated_destination_price_form():
    price_text = request.form.get("price", "")
    try:
        price = float(price_text)
        valid_price = math.isfinite(price) and price >= 0
    except ValueError:
        valid_price = False
        price = None
    if not valid_price:
        return None, "Price must be a finite nonnegative number."
    return int(price) if price.is_integer() else price, None


def owned_admin_destination(destination_id):
    if not ObjectId.is_valid(destination_id):
        return None
    return get_db().destinations.find_one({"_id": ObjectId(destination_id)})


def render_dashboard(user, error=None, status=200):
    ensure_csrf_token()
    return render_template(
        "dashboard.html",
        current_user={"name": user.get("name") or user["email"], "email": user["email"], "role": user.get("role", "user")},
        trips=user_trip_cards(user["_id"]),
        destinations=dashboard_form_destinations(),
        dashboard_error=error,
        csrf_token=session["csrf_token"],
    ), status


def render_admin(user, error=None, status=200):
    ensure_csrf_token()
    return render_template(
        "admin.html",
        current_user={"name": user.get("name") or user["email"], "email": user["email"], "role": user.get("role", "admin")},
        destinations=admin_destinations(),
        users=admin_users(),
        trips=admin_trips(),
        admin_error=error,
        csrf_token=session["csrf_token"],
    ), status


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("TRAVELMATE_SECRET_KEY") or os.environ.get("SECRET_KEY") or DEFAULT_DEV_SECRET_KEY,
        MONGODB_URI=os.environ.get("MONGODB_URI"),
        MONGODB_DATABASE=os.environ.get("MONGODB_DATABASE", "travelmate"),
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config is not None:
        app.config.update(test_config)

    @app.route("/", methods=["GET", "POST"])
    def index():
        login_error = None
        status = 200

        if request.method == "POST":
            auth_action = request.form.get("auth_action", "login")
            if auth_action == "signup":
                email, password, credential_error = validated_signup_credentials()
            else:
                email, password, credential_error = login_credentials()
            if credential_error is not None:
                login_error = credential_error
                status = 400
            else:
                try:
                    if auth_action == "signup":
                        user, signup_error = create_user_account(email, password)
                        if signup_error is not None:
                            login_error = signup_error
                            status = 409
                        else:
                            session.clear()
                            store_session_user(user)
                            ensure_csrf_token()
                            return redirect(url_for("dashboard"))
                    else:
                        user = authenticate_user(email, password)
                        if user is None:
                            login_error = "Invalid email or password."
                            status = 401
                        else:
                            session.clear()
                            store_session_user(user)
                            ensure_csrf_token()
                            if user.get("role") == "user":
                                return redirect(url_for("dashboard"))
                            return redirect(url_for("admin"))
                except (RuntimeError, PyMongoError) as error:
                    current_app.logger.error("Login unavailable: %s", type(error).__name__)
                    login_error = "Login is unavailable until MongoDB is configured and seeded."
                    status = 503

        current_user = None
        destinations = []
        if session.get("user_id"):
            current_user = {"name": session.get("user_name"), "email": session.get("user_email"), "role": session.get("user_role")}
        try:
            destinations = destination_cards()
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Home destinations unavailable: %s", type(error).__name__)
        return render_template(
            "index.html",
            destinations=destinations,
            current_user=current_user,
            login_error=login_error,
        ), status

    @app.get("/dashboard")
    def dashboard():
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if is_admin(user):
                return redirect(url_for("admin"))
            store_session_user(user)
            return render_dashboard(user)
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Dashboard unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Dashboard is unavailable until MongoDB is configured and seeded."), 503

    @app.get("/user")
    def user_redirect():
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if is_admin(user):
                return redirect(url_for("admin"))
            return redirect(url_for("dashboard"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("User redirect unavailable: %s", type(error).__name__)
            return redirect(url_for("index"))

    @app.get("/admin")
    def admin():
        try:
            user = current_user()
            if user is None:
                return "", 404
            if not is_admin(user):
                return redirect(url_for("dashboard"))
            store_session_user(user)
            return render_admin(user)
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Admin page unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Admin page is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/logout")
    def logout():
        if session.get("user_id") and validate_csrf() is not None:
            return redirect(url_for("index"))
        session.clear()
        return redirect(url_for("index"))

    @app.post("/dashboard/trips")
    def create_dashboard_trip():
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if is_admin(user):
                return redirect(url_for("admin"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_dashboard(user, csrf_error, 403)
            trip, error = validated_trip_form()
            if error is not None:
                return render_dashboard(user, error, 400)
            trip["user_id"] = user["_id"]
            get_db().trips.insert_one(trip)
            return redirect(url_for("dashboard"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Dashboard write unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Dashboard is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/dashboard/trips/<trip_id>/edit")
    def edit_dashboard_trip(trip_id):
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if is_admin(user):
                return redirect(url_for("admin"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_dashboard(user, csrf_error, 403)
            existing_trip = owned_dashboard_trip(user["_id"], trip_id)
            if existing_trip is None:
                return render_dashboard(user, "Trip not found.", 404)
            values, error = validated_trip_edit_form(existing_trip)
            if error is not None:
                return render_dashboard(user, error, 400)
            get_db().trips.find_one_and_update(
                {"_id": existing_trip["_id"], "user_id": user["_id"]},
                {"$set": values},
            )
            return redirect(url_for("dashboard"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Dashboard edit unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Dashboard is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/dashboard/trips/<trip_id>/delete")
    def delete_dashboard_trip(trip_id):
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if is_admin(user):
                return redirect(url_for("admin"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_dashboard(user, csrf_error, 403)
            existing_trip = owned_dashboard_trip(user["_id"], trip_id)
            if existing_trip is None:
                return render_dashboard(user, "Trip not found.", 404)
            get_db().trips.delete_one({"_id": existing_trip["_id"], "user_id": user["_id"]})
            return redirect(url_for("dashboard"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Dashboard delete unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Dashboard is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/admin/destinations")
    def create_admin_destination():
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if not is_admin(user):
                return redirect(url_for("dashboard"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_admin(user, csrf_error, 403)
            destination, error = validated_destination_form()
            if error is not None:
                return render_admin(user, error, 400)
            get_db().destinations.insert_one(destination)
            return redirect(url_for("admin"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Admin destination create unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Admin page is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/admin/destinations/<destination_id>/edit")
    def edit_admin_destination(destination_id):
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if not is_admin(user):
                return redirect(url_for("dashboard"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_admin(user, csrf_error, 403)
            destination = owned_admin_destination(destination_id)
            if destination is None:
                return render_admin(user, "Destination not found.", 404)
            price, error = validated_destination_price_form()
            if error is not None:
                return render_admin(user, error, 400)
            get_db().destinations.find_one_and_update({"_id": destination["_id"]}, {"$set": {"price": price}})
            return redirect(url_for("admin"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Admin destination edit unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Admin page is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/admin/destinations/<destination_id>/delete")
    def delete_admin_destination(destination_id):
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if not is_admin(user):
                return redirect(url_for("dashboard"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_admin(user, csrf_error, 403)
            destination = owned_admin_destination(destination_id)
            if destination is None:
                return render_admin(user, "Destination not found.", 404)
            if get_db().trips.find_one({"destination_id": destination["_id"]}) is not None:
                return render_admin(user, "Destination is still used by a trip and cannot be deleted.", 409)
            get_db().destinations.delete_one({"_id": destination["_id"]})
            return redirect(url_for("admin"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Admin destination delete unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Admin page is unavailable until MongoDB is configured and seeded."), 503

    @app.post("/admin/trips/<trip_id>/delete")
    def delete_admin_trip(trip_id):
        try:
            user = current_user()
            if user is None:
                return redirect(url_for("index"))
            if not is_admin(user):
                return redirect(url_for("dashboard"))
            csrf_error = validate_csrf()
            if csrf_error is not None:
                return render_admin(user, csrf_error, 403)
            if not ObjectId.is_valid(trip_id) or get_db().trips.delete_one({"_id": ObjectId(trip_id)}).deleted_count == 0:
                return render_admin(user, "Trip not found.", 404)
            return redirect(url_for("admin"))
        except (RuntimeError, PyMongoError) as error:
            current_app.logger.error("Admin trip delete unavailable: %s", type(error).__name__)
            return render_template("index.html", destinations=[], current_user=None, login_error="Admin page is unavailable until MongoDB is configured and seeded."), 503

    init_db(app)
    app.register_blueprint(trips_bp)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
