"""MongoDB access shared by trip routes and future authentication routes."""
from flask import current_app
from pymongo import MongoClient


def init_db(app):
    # Tests or Person Four may inject an existing Database here.
    if app.config.get("MONGO_DB") is not None:
        app.extensions["mongo_db"] = app.config["MONGO_DB"]
    elif app.config.get("MONGODB_URI"):
        client = MongoClient(app.config["MONGODB_URI"], serverSelectionTimeoutMS=5000)
        app.extensions["mongo_client"] = client
        app.extensions["mongo_db"] = client[app.config["MONGODB_DATABASE"]]


def get_db():
    db = current_app.extensions.get("mongo_db")
    if db is None:
        raise RuntimeError("MongoDB is not configured")
    return db
