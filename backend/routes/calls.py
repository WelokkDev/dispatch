"""
Call-related API routes.
"""
from flask import Blueprint, jsonify
from bson import ObjectId
from db import calls_collection, serialize_call

calls_bp = Blueprint("calls", __name__, url_prefix="/api/calls")


@calls_bp.route("", methods=["GET"])
def get_calls():
    """Fetch all calls from MongoDB."""
    try:
        calls = list(calls_collection.find())
        return jsonify([serialize_call(c) for c in calls])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calls_bp.route("/<call_id>", methods=["GET"])
def get_call(call_id: str):
    """Fetch a single call by ID."""
    try:
        # Try to find by 'id' field first (our custom ID)
        call = calls_collection.find_one({"id": call_id})
        if not call:
            # Try ObjectId as fallback
            try:
                call = calls_collection.find_one({"_id": ObjectId(call_id)})
            except:
                pass
        if not call:
            return jsonify({"error": "Call not found"}), 404
        return jsonify(serialize_call(call))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
