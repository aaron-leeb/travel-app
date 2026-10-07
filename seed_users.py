"""Seed sample users and trips from data.json into MongoDB."""

import os
from pathlib import Path

from bson import json_util
from dotenv import load_dotenv
from pymongo import MongoClient


def main():
    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError("Set MONGODB_URI in .env or the environment before seeding users.")

    database_name = os.environ.get("MONGODB_DATABASE", "travelmate")
    data_path = Path(__file__).with_name("data.json")
    data = json_util.loads(data_path.read_text(encoding="utf-8"))
    users = data.get("users")
    trips = data.get("trips")
    if not isinstance(users, list) or not isinstance(trips, list):
        raise ValueError("data.json must contain users and trips arrays.")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        db = client[database_name]
        user_collection = db["users"]
        trip_collection = db["trips"]
        inserted_users = 0
        sample_user_ids = {}

        for user in users:
            result = user_collection.update_one(
                {"email": user["email"]},
                {"$setOnInsert": user},
                upsert=True,
            )
            inserted_users += result.upserted_id is not None
            sample_user_ids[user["_id"]] = user["email"]

        inserted_trips = 0
        for trip in trips:
            sample_owner_id = trip.get("user_id")
            owner_email = sample_user_ids.get(sample_owner_id)
            if owner_email is None:
                raise ValueError(f"Trip {trip.get('_id')} references an unknown sample user.")

            owner = user_collection.find_one({"email": owner_email}, {"_id": 1})
            if owner is None:
                raise RuntimeError(f"Unable to find seeded trip owner {owner_email}.")

            trip["user_id"] = owner["_id"]
            result = trip_collection.update_one(
                {"_id": trip["_id"]},
                {"$setOnInsert": trip},
                upsert=True,
            )
            inserted_trips += result.upserted_id is not None

        print(
            f"Seeded {inserted_users} new user(s) and {inserted_trips} new "
            f"trip(s) into {database_name}."
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
