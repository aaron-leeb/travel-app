"""Opt-in real MongoDB test. Uses and removes a uniquely named test database."""
import os
import unittest
from uuid import uuid4
from bson import ObjectId
from pymongo import MongoClient
from app import create_app


@unittest.skipUnless(os.environ.get("TRAVELMATE_TEST_MONGODB_URI"), "Set TRAVELMATE_TEST_MONGODB_URI for live MongoDB verification")
class MongoPersistenceTest(unittest.TestCase):
    def test_crud_across_application_instances(self):
        client = MongoClient(os.environ["TRAVELMATE_TEST_MONGODB_URI"], serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        name = "travelmate_api_test_" + uuid4().hex
        db = client[name]
        try:
            owner = ObjectId()
            db.users.insert_one({"_id": owner, "name": "API test user"})
            config = {"TESTING": True, "SECRET_KEY": "test-only", "MONGO_DB": db, "MONGODB_URI": None}
            first = create_app(config).test_client()
            with first.session_transaction() as session:
                session["user_id"] = str(owner)
            token = first.get("/api/csrf-token").json["csrf_token"]
            headers = {"X-CSRF-Token": token}
            payload = {"title": "Persistence test", "destination": "Chicago", "start_date": "2026-11-10", "end_date": "2026-11-13", "budget": 700}
            created = first.post("/api/trips", json=payload, headers=headers)
            self.assertEqual(created.status_code, 201)
            trip_id = created.json["trip"]["_id"]
            second = create_app(config).test_client()
            with second.session_transaction() as session:
                session["user_id"] = str(owner)
            second_headers = {"X-CSRF-Token": second.get("/api/csrf-token").json["csrf_token"]}
            self.assertEqual(second.get("/api/trips/" + trip_id).json["trip"]["budget"], 700)
            self.assertEqual(len(second.get("/api/trips").json["trips"]), 1)
            payload["budget"] = 900
            self.assertEqual(second.put("/api/trips/" + trip_id, json=payload, headers=second_headers).status_code, 200)
            self.assertEqual(db.trips.find_one({"_id": ObjectId(trip_id)})["budget"], 900)
            self.assertEqual(second.delete("/api/trips/" + trip_id, headers=second_headers).status_code, 200)
            self.assertIsNone(db.trips.find_one({"_id": ObjectId(trip_id)}))
        finally:
            client.drop_database(name)
            client.close()
