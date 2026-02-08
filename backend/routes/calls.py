"""
Call-related API routes.
"""
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from bson import ObjectId
from db import calls_collection, serialize_call

calls_bp = Blueprint("calls", __name__, url_prefix="/api/calls")


def create_stub_call(number_masked: str, call_id: str = None) -> dict:
    """
    Create a stub call record with defaults.
    AI will populate fields as the conversation progresses.
    """
    return {
        "id": call_id or str(uuid.uuid4()),
        "numberMasked": number_masked,
        "priority": "P4",  # Default lowest, AI updates via assess_urgency()
        "incidentType": "",  # AI fills from extract_emergency()
        "incidentIcon": "",
        "status": "AI handling",
        "statusDetail": "",
        "locationLabel": "",  # AI fills from extract_location()
        "address": "",
        "city": "",
        "confidence": 0,
        "inServiceArea": True,
        "transcript": [],  # Builds up as conversation progresses
        "summary": "",  # AI generates when call ends
        "keyFacts": [],  # AI extracts
        "elapsed": "00:00",
        "aiHandling": True,
        "pin": {"lat": 0, "lng": 0},  # Updated when location is extracted
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }


@calls_bp.route("", methods=["GET"])
def get_calls():
    """Fetch all calls from MongoDB."""
    try:
        calls = list(calls_collection.find())
        return jsonify([serialize_call(c) for c in calls])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calls_bp.route("", methods=["POST"])
def create_call():
    """
    Create a new stub call in MongoDB.
    
    Request body (JSON):
        - numberMasked (required): Caller's masked phone number
        - callId (optional): Custom call ID, otherwise UUID is generated
    
    Returns the created call record.
    """
    try:
        data = request.get_json(force=True) if request.data else {}
        
        number_masked = data.get("numberMasked")
        if not number_masked:
            return jsonify({"error": "numberMasked is required"}), 400
        
        call_id = data.get("callId")
        
        # Create stub call
        stub = create_stub_call(number_masked, call_id)
        
        # Insert into MongoDB
        calls_collection.insert_one(stub)
        
        return jsonify(serialize_call(stub)), 201
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
