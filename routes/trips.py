"""Person Three: authenticated, owner-scoped trip CRUD API."""
from datetime import date
from functools import wraps
import math
import secrets

from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request, session
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from werkzeug.exceptions import BadRequest, HTTPException

from database import get_db

bp = Blueprint("trips", __name__, url_prefix="/api")
FIELDS = {"title", "destination", "start_date", "end_date", "budget", "description", "status"}


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


@bp.errorhandler(APIError)
def api_error(error):
    return jsonify(error={"code": error.code, "message": error.message}), error.status


@bp.errorhandler(Exception)
def unexpected_error(error):
    if isinstance(error, HTTPException):
        return jsonify(error={"code": "request_error", "message": error.description}), error.code
    # Never expose database connection strings or exception contents in responses/logs.
    current_app.logger.error("Trip API failure: %s", type(error).__name__)
    status = 503 if isinstance(error, (PyMongoError, RuntimeError)) else 500
    return jsonify(error={"code": "service_unavailable" if status == 503 else "internal_error",
                          "message": "Service unavailable. Please try again later."}), status


def authenticated(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        # Person Four sets this ONLY after verifying the user's password.
        user_id = session.get("user_id")
        if not isinstance(user_id, str) or not ObjectId.is_valid(user_id):
            raise APIError(401, "unauthenticated", "Please log in first.")
        g.user_id = ObjectId(user_id)
        # Verify the signed-session identity still refers to a real account.
        if get_db().users.find_one({"_id": g.user_id}, {"_id": 1}) is None:
            raise APIError(401, "unauthenticated", "Please log in again.")
        if request.method in {"POST", "PUT", "DELETE"}:
            expected = session.get("csrf_token")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not isinstance(expected, str) or not secrets.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8")):
                raise APIError(403, "csrf_failed", "Refresh your session token and try again.")
        return view(*args, **kwargs)
    return wrapped


def owned_filter(trip_id):
    if not ObjectId.is_valid(trip_id):
        raise APIError(400, "invalid_id", "Trip ID must be a valid ObjectId.")
    return {"_id": ObjectId(trip_id), "user_id": g.user_id}


def serialize(trip):
    return {"_id": str(trip["_id"]), "user_id": str(trip["user_id"]),
            **{field: trip.get(field) for field in sorted(FIELDS)}}


def validated_payload():
    if not request.is_json:
        raise APIError(415, "unsupported_media_type", "Use Content-Type: application/json.")
    try:
        data = request.get_json()
    except BadRequest:
        raise APIError(400, "invalid_input", "Request body must contain valid JSON.") from None
    if not isinstance(data, dict):
        raise APIError(400, "invalid_input", "Request body must be a JSON object.")
    if set(data) - FIELDS:
        raise APIError(400, "invalid_input", "Unknown fields or ownership changes are not allowed.")
    result = {}
    for field, limit in [("title", 200), ("destination", 200), ("description", 5000)]:
        value = data.get(field, "")
        if not isinstance(value, str) or len(value.strip()) > limit or (field != "description" and not value.strip()):
            raise APIError(400, "invalid_input", f"{field} must be text (maximum {limit} characters)" + ("." if field == "description" else " and cannot be empty."))
        result[field] = value.strip()
    for field in ["start_date", "end_date"]:
        value = data.get(field)
        try:
            if not isinstance(value, str) or len(value) != 10 or date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError:
            raise APIError(400, "invalid_input", f"{field} must be a valid YYYY-MM-DD date.") from None
        result[field] = value
    if result["end_date"] < result["start_date"]:
        raise APIError(400, "invalid_input", "end_date must be on or after start_date.")
    budget = data.get("budget")
    try:
        valid_budget = type(budget) in (int, float) and math.isfinite(budget) and budget >= 0
    except OverflowError:
        valid_budget = False
    if not valid_budget:
        raise APIError(400, "invalid_input", "budget must be a finite nonnegative number.")
    result["budget"] = budget
    status = data.get("status", "Planned")
    if not isinstance(status, str) or status not in {"Planned", "Ongoing", "Completed"}:
        raise APIError(400, "invalid_input", "status must be Planned, Ongoing, or Completed.")
    result["status"] = status
    return result


def require_trip(trip):
    if trip is None:
        raise APIError(404, "not_found", "Trip not found.")
    return trip


@bp.get("/csrf-token")
@authenticated
def csrf_token():
    if not session.get("csrf_token"):
        session["csrf_token"] = secrets.token_hex(32)
    response = jsonify(csrf_token=session["csrf_token"])
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/trips")
@authenticated
def list_trips():
    trips = get_db().trips.find({"user_id": g.user_id}).sort("_id", -1)
    return jsonify(trips=[serialize(trip) for trip in trips])


@bp.get("/trips/<trip_id>")
@authenticated
def read_trip(trip_id):
    trip = require_trip(get_db().trips.find_one(owned_filter(trip_id)))
    return jsonify(trip=serialize(trip))


@bp.post("/trips")
@authenticated
def create_trip():
    trip = validated_payload()
    trip["user_id"] = g.user_id
    trip["_id"] = get_db().trips.insert_one(trip).inserted_id
    return jsonify(trip=serialize(trip)), 201


@bp.put("/trips/<trip_id>")
@authenticated
def update_trip(trip_id):
    query = owned_filter(trip_id)
    values = validated_payload()
    trip = require_trip(get_db().trips.find_one_and_update(
        query, {"$set": values}, return_document=ReturnDocument.AFTER))
    return jsonify(trip=serialize(trip))


@bp.delete("/trips/<trip_id>")
@authenticated
def delete_trip(trip_id):
    # Trip deletion only; Person Five must agree on activity lifecycle before release.
    result = get_db().trips.delete_one(owned_filter(trip_id))
    if result.deleted_count == 0:
        raise APIError(404, "not_found", "Trip not found.")
    return jsonify(deleted=True)
