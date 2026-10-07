"""Run: python -m unittest discover -s tests -v (no live MongoDB required)."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from bson import ObjectId
from pymongo.errors import AutoReconnect
from app import create_app


class TripsCollection:
    """Small in-memory test double; production always uses PyMongo."""
    def __init__(self):
        self.documents = {}

    def insert_one(self, doc):
        doc["_id"] = ObjectId()
        self.documents[doc["_id"]] = copy.deepcopy(doc)
        return SimpleNamespace(inserted_id=doc["_id"])

    def find_one(self, query):
        return next((copy.deepcopy(d) for d in self.documents.values()
                     if all(d.get(k) == v for k, v in query.items())), None)

    def find(self, query):
        docs = [copy.deepcopy(d) for d in self.documents.values()
                if all(d.get(k) == v for k, v in query.items())]
        return SimpleNamespace(sort=lambda *args: sorted(docs, key=lambda d: d["_id"], reverse=True))

    def find_one_and_update(self, query, update, **kwargs):
        doc = self.find_one(query)
        if doc is not None:
            self.documents[doc["_id"]].update(update["$set"])
            return copy.deepcopy(self.documents[doc["_id"]])
        return None

    def delete_one(self, query):
        doc = self.find_one(query)
        if doc:
            del self.documents[doc["_id"]]
        return SimpleNamespace(deleted_count=int(doc is not None))


class TripAPITests(unittest.TestCase):
    def setUp(self):
        self.owner, self.other = ObjectId(), ObjectId()
        self.db = SimpleNamespace(trips=TripsCollection(), users=Mock())
        self.db.users.find_one.side_effect = lambda q, *args: {"_id": q["_id"]} if q["_id"] in {self.owner, self.other} else None
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-only-secret",
                               "MONGO_DB": self.db, "MONGODB_URI": None})
        self.client = self.app.test_client()
        self.login(self.owner)
        self.payload = {"title": " Chicago Weekend ", "destination": "Chicago, IL",
                        "start_date": "2026-11-10", "end_date": "2026-11-13", "budget": 700}

    def login(self, user):
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = str(user)
        response = self.client.get("/api/csrf-token")
        self.headers = {"X-CSRF-Token": response.json["csrf_token"]}

    def create(self):
        response = self.client.post("/api/trips", json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        return response.json["trip"]["_id"]

    def test_complete_crud_and_repeat_reads(self):
        self.assertEqual(self.client.get("/api/trips").json, {"trips": []})
        trip_id = self.create()
        self.assertEqual(self.client.get("/api/trips").json["trips"][0]["title"], "Chicago Weekend")
        trip = self.client.get("/api/trips/" + trip_id).json["trip"]
        self.assertEqual(trip["user_id"], str(self.owner))
        self.assertEqual(trip["status"], "Planned")
        self.payload["budget"] = 900
        response = self.client.put("/api/trips/" + trip_id, json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/trips/" + trip_id).json["trip"]["budget"], 900)
        self.assertEqual(self.client.delete("/api/trips/" + trip_id, headers=self.headers).json, {"deleted": True})
        self.assertEqual(self.client.get("/api/trips/" + trip_id).status_code, 404)

    def test_other_user_cannot_read_update_delete(self):
        trip_id = self.create()
        self.login(self.other)
        self.assertEqual(self.client.get("/api/trips").json, {"trips": []})
        path = "/api/trips/" + trip_id
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.put(path, json=self.payload, headers=self.headers).status_code, 404)
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 404)
        self.assertIsNotNone(self.db.trips.find_one({"_id": ObjectId(trip_id)}))

    def test_unauthenticated_and_deleted_account(self):
        for identity in [None, "bad", str(ObjectId())]:
            with self.client.session_transaction() as session:
                session.clear()
                if identity is not None:
                    session["user_id"] = identity
            for method, path in [("GET", "/api/trips"), ("GET", "/api/trips/" + str(ObjectId())),
                                 ("POST", "/api/trips"), ("PUT", "/api/trips/" + str(ObjectId())),
                                 ("DELETE", "/api/trips/" + str(ObjectId()))]:
                with self.subTest(identity=identity, method=method):
                    self.assertEqual(self.client.open(path, method=method).status_code, 401)

    def test_invalid_payloads(self):
        cases = [None, [], {}, {**self.payload, "user_id": str(self.other)},
                 {**self.payload, "title": " "}, {**self.payload, "destination": 3},
                 {**self.payload, "start_date": "2026-02-30"},
                 {**self.payload, "end_date": "2026-01-01"},
                 {**self.payload, "budget": True}, {**self.payload, "budget": -1},
                 {**self.payload, "budget": float("inf")}, {**self.payload, "budget": 10**400},
                 {**self.payload, "status": []}, {**self.payload, "description": 123}]
        for payload in cases:
            with self.subTest(payload=payload):
                import json
                response = self.client.post("/api/trips", data=json.dumps(payload),
                                            content_type="application/json", headers=self.headers)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)
        self.assertEqual(len(self.db.trips.documents), 0)

    def test_bad_json_content_type_ids_and_missing_records(self):
        self.assertEqual(self.client.post("/api/trips", data="{", content_type="application/json", headers=self.headers).status_code, 400)
        self.assertEqual(self.client.post("/api/trips", data="hello", headers=self.headers).status_code, 415)
        for method in ["GET", "PUT", "DELETE"]:
            for trip_id, expected in [("bad-id", 400), (str(ObjectId()), 404)]:
                response = self.client.open("/api/trips/" + trip_id, method=method,
                                            json=self.payload, headers=self.headers)
                self.assertEqual(response.status_code, expected)

    def test_csrf_and_failure_redaction(self):
        self.assertEqual(self.client.post("/api/trips", json=self.payload).status_code, 403)
        self.assertEqual(self.client.post("/api/trips", json=self.payload, headers={"X-CSRF-Token": "wrong"}).status_code, 403)
        self.db.users.find_one.side_effect = AutoReconnect("secret connection string")
        response = self.client.get("/api/trips")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.get_data(as_text=True))

    def test_homepage_without_database(self):
        app = create_app({"TESTING": True, "MONGODB_URI": None})
        self.assertEqual(app.test_client().get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
