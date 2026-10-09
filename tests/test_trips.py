"""Run: python -m unittest discover -s tests -v (no live MongoDB required)."""
import copy
import unittest
from types import SimpleNamespace

from bson import ObjectId
from pymongo.errors import AutoReconnect
from werkzeug.security import generate_password_hash

from app import create_app


class CursorDouble:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, field, direction):
        reverse = direction == -1
        return sorted(self.docs, key=lambda doc: doc[field], reverse=reverse)

    def __iter__(self):
        return iter(self.docs)


class CollectionDouble:
    """Small in-memory test double; production always uses PyMongo."""

    def __init__(self, docs=None):
        self.documents = {}
        for doc in docs or []:
            self.documents[doc["_id"]] = copy.deepcopy(doc)

    def insert_one(self, doc):
        stored = copy.deepcopy(doc)
        stored["_id"] = stored.get("_id", ObjectId())
        self.documents[stored["_id"]] = stored
        return SimpleNamespace(inserted_id=stored["_id"])

    def find_one(self, query, projection=None):
        doc = next(
            (
                copy.deepcopy(document)
                for document in self.documents.values()
                if all(document.get(key) == value for key, value in query.items())
            ),
            None,
        )
        if doc is None:
            return None
        if projection == {"_id": 1}:
            return {"_id": doc["_id"]}
        return doc

    def find(self, query):
        docs = [
            copy.deepcopy(document)
            for document in self.documents.values()
            if all(document.get(key) == value for key, value in query.items())
        ]
        return CursorDouble(docs)

    def find_one_and_update(self, query, update, **kwargs):
        doc = self.find_one(query)
        if doc is None:
            return None
        self.documents[doc["_id"]].update(copy.deepcopy(update["$set"]))
        return copy.deepcopy(self.documents[doc["_id"]])

    def delete_one(self, query):
        doc = self.find_one(query)
        if doc is not None:
            del self.documents[doc["_id"]]
        return SimpleNamespace(deleted_count=int(doc is not None))


class TripAPITests(unittest.TestCase):
    def setUp(self):
        self.owner, self.admin = ObjectId(), ObjectId()
        self.chicago, self.venice = ObjectId(), ObjectId()
        self.db = SimpleNamespace(
            trips=CollectionDouble(),
            destinations=CollectionDouble(
                [
                    {"_id": self.chicago, "name": "Chicago, IL", "price": 199},
                    {"_id": self.venice, "name": "Venice", "price": 249},
                ]
            ),
            users=CollectionDouble(
                [
                    {
                        "_id": self.owner,
                        "email": "user@example.com",
                        "name": "Test User",
                        "password_hash": generate_password_hash("testuser"),
                        "active": True,
                        "role": "user",
                    },
                    {
                        "_id": self.admin,
                        "email": "admin@example.com",
                        "name": "Test Admin",
                        "password_hash": generate_password_hash("testadmin"),
                        "active": True,
                        "role": "admin",
                    },
                ]
            ),
        )
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-only-secret", "MONGO_DB": self.db, "MONGODB_URI": None})
        self.client = self.app.test_client()
        self.login(self.owner)
        self.payload = {
            "title": " Chicago Weekend ",
            "destination_id": str(self.chicago),
            "start_date": "2026-11-10",
            "end_date": "2026-11-13",
            "budget": 700,
        }

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
        listed_trip = self.client.get("/api/trips").json["trips"][0]
        self.assertEqual(listed_trip["title"], "Chicago Weekend")
        self.assertEqual(listed_trip["destination"]["name"], "Chicago, IL")
        trip = self.client.get("/api/trips/" + trip_id).json["trip"]
        self.assertEqual(trip["user_id"], str(self.owner))
        self.assertEqual(trip["status"], "Planned")
        self.assertEqual(trip["destination_id"], str(self.chicago))
        self.payload["budget"] = 900
        self.payload["destination_id"] = str(self.venice)
        response = self.client.put("/api/trips/" + trip_id, json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        updated_trip = self.client.get("/api/trips/" + trip_id).json["trip"]
        self.assertEqual(updated_trip["budget"], 900)
        self.assertEqual(updated_trip["destination"]["name"], "Venice")
        self.assertEqual(self.client.delete("/api/trips/" + trip_id, headers=self.headers).json, {"deleted": True})
        self.assertEqual(self.client.get("/api/trips/" + trip_id).status_code, 404)

    def test_destinations_list_and_admin_create(self):
        response = self.client.get("/api/destinations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([destination["name"] for destination in response.json["destinations"]], ["Chicago, IL", "Venice"])

        forbidden = self.client.post("/api/destinations", json={"name": "Cyprus", "price": 239}, headers=self.headers)
        self.assertEqual(forbidden.status_code, 403)

        self.login(self.admin)
        created = self.client.post("/api/destinations", json={"name": "Cyprus", "price": 239}, headers=self.headers)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["destination"]["name"], "Cyprus")
        duplicate = self.client.post("/api/destinations", json={"name": "cyprus", "price": 300}, headers=self.headers)
        self.assertEqual(duplicate.status_code, 409)

    def test_other_user_cannot_read_update_delete(self):
        trip_id = self.create()
        self.login(self.admin)
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
            for method, path in [
                ("GET", "/api/trips"),
                ("GET", "/api/trips/" + str(ObjectId())),
                ("GET", "/api/destinations"),
                ("POST", "/api/trips"),
                ("POST", "/api/destinations"),
                ("PUT", "/api/trips/" + str(ObjectId())),
                ("DELETE", "/api/trips/" + str(ObjectId())),
            ]:
                with self.subTest(identity=identity, method=method):
                    self.assertEqual(self.client.open(path, method=method).status_code, 401)

    def test_invalid_payloads(self):
        cases = [
            None,
            [],
            {},
            {**self.payload, "user_id": str(self.admin)},
            {**self.payload, "title": " "},
            {**self.payload, "destination_id": 3},
            {**self.payload, "destination_id": str(ObjectId())},
            {**self.payload, "start_date": "2026-02-30"},
            {**self.payload, "end_date": "2026-01-01"},
            {**self.payload, "budget": True},
            {**self.payload, "budget": -1},
            {**self.payload, "budget": float("inf")},
            {**self.payload, "budget": 10**400},
            {**self.payload, "status": []},
            {**self.payload, "description": 123},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                import json

                response = self.client.post("/api/trips", data=json.dumps(payload), content_type="application/json", headers=self.headers)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)
        self.assertEqual(len(self.db.trips.documents), 0)

    def test_bad_json_content_type_ids_and_missing_records(self):
        self.assertEqual(self.client.post("/api/trips", data="{", content_type="application/json", headers=self.headers).status_code, 400)
        self.assertEqual(self.client.post("/api/trips", data="hello", headers=self.headers).status_code, 415)
        for method in ["GET", "PUT", "DELETE"]:
            for trip_id, expected in [("bad-id", 400), (str(ObjectId()), 404)]:
                response = self.client.open("/api/trips/" + trip_id, method=method, json=self.payload, headers=self.headers)
                self.assertEqual(response.status_code, expected)

    def test_csrf_and_failure_redaction(self):
        self.assertEqual(self.client.post("/api/trips", json=self.payload).status_code, 403)
        self.assertEqual(self.client.post("/api/trips", json=self.payload, headers={"X-CSRF-Token": "wrong"}).status_code, 403)
        self.db.users.find_one = lambda *args, **kwargs: (_ for _ in ()).throw(AutoReconnect("secret connection string"))
        response = self.client.get("/api/trips")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.get_data(as_text=True))

    def test_homepage_without_database(self):
        app = create_app({"TESTING": True, "MONGODB_URI": None})
        self.assertEqual(app.test_client().get("/").status_code, 200)

    def test_homepage_login_accepts_demo_user_and_admin(self):
        user_response = self.client.post("/", data={"email": "user@example.com", "password": "testuser"})
        self.assertEqual(user_response.status_code, 302)
        self.assertTrue(user_response.headers["Location"].endswith("/dashboard"))
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], str(self.owner))
            self.assertEqual(session["user_role"], "user")

        admin_response = self.client.post("/", data={"email": "admin@example.com", "password": "testadmin"})
        self.assertEqual(admin_response.status_code, 302)
        self.assertTrue(admin_response.headers["Location"].endswith("/admin"))
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], str(self.admin))
            self.assertEqual(session["user_role"], "admin")

    def test_homepage_signup_creates_only_normal_users(self):
        response = self.client.post(
            "/",
            data={"email": "newuser@example.com", "password": "testpass1", "auth_action": "signup"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/dashboard"))

        created_user = self.db.users.find_one({"email": "newuser@example.com"})
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user["role"], "user")
        self.assertTrue(created_user["active"])
        self.assertNotEqual(created_user["password_hash"], "testpass1")

        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], str(created_user["_id"]))
            self.assertEqual(session["user_role"], "user")

    def test_homepage_signup_rejects_duplicate_email(self):
        response = self.client.post(
            "/",
            data={"email": "user@example.com", "password": "testpass1", "auth_action": "signup"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("already exists", response.get_data(as_text=True))

    def test_dashboard_shows_destinations_and_adds_trip(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Welcome, Test User", page)
        self.assertIn("Chicago, IL ($199)", page)
        self.assertNotIn(">Home<", page)
        self.assertNotIn(">Dashboard<", page)
        self.assertNotIn(">Destinations<", page)
        self.assertNotIn(">Login<", page)
        self.assertNotIn("Browse destinations", page)

        created = self.client.post(
            "/dashboard/trips",
            data={
                "csrf_token": self.headers["X-CSRF-Token"],
                "title": "Holiday Break",
                "destination_id": str(self.chicago),
                "start_date": "2026-12-20",
                "end_date": "2026-12-24",
                "budget": "800",
                "status": "Planned",
                "description": "Family trip",
            },
        )
        self.assertEqual(created.status_code, 302)
        self.assertTrue(created.headers["Location"].endswith("/dashboard"))
        dashboard = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Holiday Break", dashboard)
        self.assertIn("Chicago, IL", dashboard)

    def test_dashboard_edits_and_deletes_trip_without_changing_destination(self):
        trip_id = self.create()
        created_trip = self.db.trips.find_one({"_id": ObjectId(trip_id)})
        response = self.client.post(
            f"/dashboard/trips/{trip_id}/edit",
            data={
                "csrf_token": self.headers["X-CSRF-Token"],
                "title": "Updated Weekend",
                "start_date": "2026-11-11",
                "end_date": "2026-11-14",
                "budget": "950",
                "status": "Ongoing",
                "description": "Updated notes",
            },
        )
        self.assertEqual(response.status_code, 302)
        updated_trip = self.db.trips.find_one({"_id": ObjectId(trip_id)})
        self.assertEqual(updated_trip["title"], "Updated Weekend")
        self.assertEqual(updated_trip["destination_id"], created_trip["destination_id"])
        self.assertEqual(updated_trip["budget"], 950)
        dashboard = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Updated Weekend", dashboard)
        self.assertIn("Chicago, IL", dashboard)

        deleted = self.client.post(
            f"/dashboard/trips/{trip_id}/delete",
            data={"csrf_token": self.headers["X-CSRF-Token"]},
        )
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(self.db.trips.find_one({"_id": ObjectId(trip_id)}))

    def test_dashboard_requires_login(self):
        with self.client.session_transaction() as session:
            session.clear()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/"))

    def test_logout_clears_session_from_dashboard(self):
        page = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Log out", page)
        response = self.client.post("/logout", data={"csrf_token": self.headers["X-CSRF-Token"]})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/"))
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)
        redirect = self.client.get("/dashboard")
        self.assertEqual(redirect.status_code, 302)
        self.assertTrue(redirect.headers["Location"].endswith("/"))
        self.assertEqual(self.client.get("/api/trips").status_code, 401)

    def test_admin_page_requires_admin_and_manages_destinations(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/dashboard"))

        self.login(self.admin)
        page = self.client.get("/admin")
        self.assertEqual(page.status_code, 200)
        text = page.get_data(as_text=True)
        self.assertIn("Manage destinations", text)
        self.assertIn("Chicago, IL", text)
        add_form = text.split('action="/admin/destinations"', 1)[1].split("</form>", 1)[0]
        self.assertIn('<input name="name"', add_form)
        self.assertIn('<input name="price"', add_form)

        created = self.client.post(
            "/admin/destinations",
            data={"csrf_token": self.headers["X-CSRF-Token"], "name": "Cyprus", "price": "239"},
        )
        self.assertEqual(created.status_code, 302)
        self.assertEqual(len(self.db.destinations.documents), 3)
        new_destination = next(destination for destination in self.db.destinations.documents.values() if destination["name"] == "Cyprus")

        edited = self.client.post(
            f"/admin/destinations/{new_destination['_id']}/edit",
            data={"csrf_token": self.headers["X-CSRF-Token"], "price": "255"},
        )
        self.assertEqual(edited.status_code, 302)
        self.assertEqual(self.db.destinations.find_one({"_id": new_destination["_id"]})["price"], 255)

        deleted = self.client.post(
            f"/admin/destinations/{new_destination['_id']}/delete",
            data={"csrf_token": self.headers["X-CSRF-Token"]},
        )
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(self.db.destinations.find_one({"_id": new_destination["_id"]}))

    def test_admin_api_lists_users_and_all_trips_and_deletes_any_trip(self):
        trip_id = self.create()
        for method, path in [
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/trips"),
            ("DELETE", "/api/admin/trips/" + trip_id),
        ]:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.client.open(path, method=method, headers=self.headers).status_code, 403)

        self.login(self.admin)
        users = self.client.get("/api/admin/users").json["users"]
        self.assertEqual(
            users,
            [
                {"_id": str(self.admin), "name": "Test Admin", "email": "admin@example.com", "role": "admin", "active": True},
                {"_id": str(self.owner), "name": "Test User", "email": "user@example.com", "role": "user", "active": True},
            ],
        )

        trips = self.client.get("/api/admin/trips").json["trips"]
        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0]["_id"], trip_id)
        self.assertEqual(trips[0]["owner_email"], "user@example.com")
        self.assertEqual(trips[0]["destination_name"], "Chicago, IL")

        self.assertEqual(self.client.delete("/api/admin/trips/bad-id", headers=self.headers).status_code, 400)
        self.assertEqual(self.client.delete("/api/admin/trips/" + trip_id, headers=self.headers).json, {"deleted": True})
        self.assertIsNone(self.db.trips.find_one({"_id": ObjectId(trip_id)}))
        self.assertEqual(self.client.delete("/api/admin/trips/" + trip_id, headers=self.headers).status_code, 404)

    def test_admin_page_shows_users_and_trips_and_deletes_trip(self):
        trip_id = self.create()
        denied = self.client.post(f"/admin/trips/{trip_id}/delete", data={"csrf_token": self.headers["X-CSRF-Token"]})
        self.assertTrue(denied.headers["Location"].endswith("/dashboard"))
        self.assertIsNotNone(self.db.trips.find_one({"_id": ObjectId(trip_id)}))

        self.login(self.admin)
        page = self.client.get("/admin").get_data(as_text=True)
        self.assertIn('<h2>Users</h2><span class="count">2</span>', page)
        self.assertIn("user@example.com", page)
        self.assertIn('<h2>All trips</h2><span class="count">1</span>', page)
        self.assertIn("Chicago Weekend", page)
        self.assertNotIn("scrypt", page)

        deleted = self.client.post(f"/admin/trips/{trip_id}/delete", data={"csrf_token": self.headers["X-CSRF-Token"]})
        self.assertEqual(deleted.status_code, 302)
        self.assertIsNone(self.db.trips.find_one({"_id": ObjectId(trip_id)}))
        self.assertIn('<h2>All trips</h2><span class="count">0</span>', self.client.get("/admin").get_data(as_text=True))

    def test_admin_cannot_delete_destination_in_use(self):
        self.login(self.admin)
        self.create()
        response = self.client.post(
            f"/admin/destinations/{self.chicago}/delete",
            data={"csrf_token": self.headers["X-CSRF-Token"]},
        )
        self.assertEqual(response.status_code, 409)
        self.assertIsNotNone(self.db.destinations.find_one({"_id": self.chicago}))


if __name__ == "__main__":
    unittest.main()
