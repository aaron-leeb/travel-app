"""Opt-in live MongoDB test for seeding sample users and trips."""

import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import check_password_hash

import seed_users


@unittest.skipUnless(
    os.environ.get("TRAVELMATE_TEST_MONGODB_URI"),
    "Set TRAVELMATE_TEST_MONGODB_URI to run live MongoDB seed verification.",
)
class SeedUsersMongoIntegrationTest(unittest.TestCase):
    def test_seeds_user_and_owned_trip_idempotently(self):
        database_name = "travelmate_seed_test_" + uuid4().hex
        uri = os.environ["TRAVELMATE_TEST_MONGODB_URI"]
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)

        try:
            client.admin.command("ping")
            with patch.dict(
                os.environ,
                {
                    "MONGODB_URI": uri,
                    "MONGODB_DATABASE": database_name,
                },
            ):
                seed_users.main()

            db = client[database_name]
            user = db.users.find_one({"email": "user@example.com"})
            self.assertIsNotNone(user)
            self.assertEqual(user["role"], "user")
            self.assertTrue(check_password_hash(user["password_hash"], "testuser"))

            trip = db.trips.find_one({"user_id": user["_id"]})
            self.assertIsNotNone(trip)
            self.assertEqual(trip["title"], "Chicago Weekend")
            self.assertIsInstance(trip["_id"], ObjectId)

            with patch.dict(
                os.environ,
                {
                    "MONGODB_URI": uri,
                    "MONGODB_DATABASE": database_name,
                },
            ):
                seed_users.main()

            self.assertEqual(db.users.count_documents({}), 2)
            self.assertEqual(db.trips.count_documents({}), 1)
        finally:
            client.drop_database(database_name)
            client.close()


if __name__ == "__main__":
    unittest.main()
