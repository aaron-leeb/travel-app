"""Authenticated trip and destination APIs."""
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
TRIP_FIELDS = {"title", "destination_id", "start_date", "end_date", "budget", "description", "status"}


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
    current_app.logger.error("Trip API failure: %s", type(error).__name__)
    status = 503 if isinstance(error, (PyMongoError, RuntimeError)) else 500
    return jsonify(
        error={
            "code": "service_unavailable" if status == 503 else "internal_error",
            "message": "Service unavailable. Please try again later.",
        }
    ), status


def authenticated(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not isinstance(user_id, str) or not ObjectId.is_valid(user_id):
            raise APIError(401, "unauthenticated", "Please log in first.")
        g.user_id = ObjectId(user_id)
        g.user = get_db().users.find_one({"_id": g.user_id})
        if g.user is None:
            raise APIError(401, "unauthenticated", "Please log in again.")
        if request.method in {"POST", "PUT", "DELETE"}:
            expected = session.get("csrf_token")
            supplied = request.headers.get("X-CSRF-Token", "")
            if not isinstance(expected, str) or not secrets.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8")):
                raise APIError(403, "csrf_failed", "Refresh your session token and try again.")
        return view(*args, **kwargs)
    return wrapped


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user.get("role") != "admin":
            raise APIError(403, "forbidden", "Admin access is required.")
        return view(*args, **kwargs)
    return wrapped


def owned_filter(trip_id):
    if not ObjectId.is_valid(trip_id):
        raise APIError(400, "invalid_id", "Trip ID must be a valid ObjectId.")
    return {"_id": ObjectId(trip_id), "user_id": g.user_id}


def serialize_destination(destination):
    return {
        "_id": str(destination["_id"]),
        "name": destination["name"],
        "price": destination["price"],
    }


def destination_by_id(destination_id):
    destination = get_db().destinations.find_one({"_id": destination_id})
    if destination is None:
        raise APIError(400, "invalid_input", "destination_id must reference an existing destination.")
    return destination


def serialize_trip(trip):
    destination = destination_by_id(trip["destination_id"])
    return {
        "_id": str(trip["_id"]),
        "user_id": str(trip["user_id"]),
        "destination_id": str(trip["destination_id"]),
        "destination": serialize_destination(destination),
        "title": trip["title"],
        "start_date": trip["start_date"],
        "end_date": trip["end_date"],
        "budget": trip["budget"],
        "description": trip.get("description", ""),
        "status": trip["status"],
    }


def json_object():
    if not request.is_json:
        raise APIError(415, "unsupported_media_type", "Use Content-Type: application/json.")
    try:
        data = request.get_json()
    except BadRequest:
        raise APIError(400, "invalid_input", "Request body must contain valid JSON.") from None
    if not isinstance(data, dict):
        raise APIError(400, "invalid_input", "Request body must be a JSON object.")
    return data


def validated_text(data, field, limit, optional=False):
    value = data.get(field, "")
    if optional and field not in data:
        return ""
    if not isinstance(value, str):
        raise APIError(400, "invalid_input", f"{field} must be text.")
    text = value.strip()
    if len(text) > limit or (not optional and not text):
        raise APIError(
            400,
            "invalid_input",
            f"{field} must be text (maximum {limit} characters)" + ("." if optional else " and cannot be empty."),
        )
    return text


def validated_money(value, field):
    try:
        valid_money = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid_money = False
    if not valid_money:
        raise APIError(400, "invalid_input", f"{field} must be a finite nonnegative number.")
    return value


def validated_trip_payload():
    data = json_object()
    if set(data) - TRIP_FIELDS:
        raise APIError(400, "invalid_input", "Unknown fields or ownership changes are not allowed.")
    result = {
        "title": validated_text(data, "title", 200),
        "description": validated_text(data, "description", 5000, optional=True),
    }
    destination_id = data.get("destination_id")
    if not isinstance(destination_id, str) or not ObjectId.is_valid(destination_id):
        raise APIError(400, "invalid_input", "destination_id must be a valid ObjectId string.")
    result["destination_id"] = destination_by_id(ObjectId(destination_id))["_id"]
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
    result["budget"] = validated_money(data.get("budget"), "budget")
    status = data.get("status", "Planned")
    if not isinstance(status, str) or status not in {"Planned", "Ongoing", "Completed"}:
        raise APIError(400, "invalid_input", "status must be Planned, Ongoing, or Completed.")
    result["status"] = status
    return result


def validated_destination_payload():
    data = json_object()
    allowed_fields = {"name", "price"}
    if set(data) - allowed_fields:
        raise APIError(400, "invalid_input", "Unknown destination fields are not allowed.")
    name = validated_text(data, "name", 200)
    for existing in get_db().destinations.find({}):
        if existing.get("name", "").strip().casefold() == name.casefold():
            raise APIError(409, "conflict", "A destination with that name already exists.")
    return {"name": name, "price": validated_money(data.get("price"), "price")}


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


@bp.get("/destinations")
@authenticated
def list_destinations():
    destinations = get_db().destinations.find({}).sort("name", 1)
    return jsonify(destinations=[serialize_destination(destination) for destination in destinations])


@bp.post("/destinations")
@authenticated
@require_admin
def create_destination():
    destination = validated_destination_payload()
    destination["_id"] = get_db().destinations.insert_one(destination).inserted_id
    return jsonify(destination=serialize_destination(destination)), 201


@bp.get("/trips")
@authenticated
def list_trips():
    trips = get_db().trips.find({"user_id": g.user_id}).sort("_id", -1)
    return jsonify(trips=[serialize_trip(trip) for trip in trips])


@bp.get("/trips/<trip_id>")
@authenticated
def read_trip(trip_id):
    trip = require_trip(get_db().trips.find_one(owned_filter(trip_id)))
    return jsonify(trip=serialize_trip(trip))


@bp.post("/trips")
@authenticated
def create_trip():
    trip = validated_trip_payload()
    trip["user_id"] = g.user_id
    trip["_id"] = get_db().trips.insert_one(trip).inserted_id
    return jsonify(trip=serialize_trip(trip)), 201


@bp.put("/trips/<trip_id>")
@authenticated
def update_trip(trip_id):
    query = owned_filter(trip_id)
    values = validated_trip_payload()
    trip = require_trip(
        get_db().trips.find_one_and_update(query, {"$set": values}, return_document=ReturnDocument.AFTER)
    )
    return jsonify(trip=serialize_trip(trip))


@bp.delete("/trips/<trip_id>")
@authenticated
def delete_trip(trip_id):
    result = get_db().trips.delete_one(owned_filter(trip_id))
    if result.deleted_count == 0:
        raise APIError(404, "not_found", "Trip not found.")
    return jsonify(deleted=True)
