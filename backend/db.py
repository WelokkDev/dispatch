"""
Centralized MongoDB connection.
Import `db` or `calls_collection` from here in routes/services.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.environ.get("MONGODB_URI"))
db = mongo_client["dispatch"]
calls_collection = db["calls"]


def serialize_call(call: dict) -> dict:
    """Convert MongoDB document to JSON-serializable format."""
    if call is None:
        return None
    # Convert ObjectId to string, use 'id' field if exists, otherwise use _id
    call_dict = dict(call)
    if "_id" in call_dict:
        if "id" not in call_dict:
            call_dict["id"] = str(call_dict["_id"])
        del call_dict["_id"]
    # Remove MongoDB timestamp fields if present
    call_dict.pop("createdAt", None)
    call_dict.pop("updatedAt", None)
    return call_dict
