"""
Centralized MongoDB connection.
Import `db` or `calls_collection` from here in routes/services.
"""
import os
from datetime import datetime
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


def _mask_number(phone_number: str) -> str:
    """Mask caller ID to last 4 digits."""
    if not phone_number:
        return "Unknown"
    return f"XXX-XXX-{str(phone_number).strip()[-4:]}"


def _state_to_call_doc(call_id: str, state_data: dict, now: datetime) -> dict:
    """Build a full call document from handle_caller_speech result."""
    urgency_to_priority = {"P0": "P1", "P1": "P2", "P2": "P3", "P3": "P4"}
    status_map = {
        "in_progress": "AI handling",
        "transferred": "AI → Human Takeover",
        "completed": "Completed",
    }
    priority = "P4"
    if state_data.get("urgency"):
        priority = urgency_to_priority.get(state_data["urgency"], "P4")
    emergency = state_data.get("emergency") or ""
    if emergency == "undefined":
        emergency = ""
    location = state_data.get("location") or ""
    if location == "undefined":
        location = ""
    status = status_map.get(state_data.get("status"), "AI handling")
    transcript = parse_transcript(state_data["transcript"]) if state_data.get("transcript") else []

    return {
        "id": call_id,
        "numberMasked": _mask_number(state_data.get("number") or ""),
        "priority": priority,
        "incidentType": emergency,
        "incidentIcon": "",
        "status": status,
        "statusDetail": "",
        "locationLabel": location,
        "address": location,
        "city": "",
        "confidence": state_data.get("confidence", 0),
        "inServiceArea": True,
        "transcript": transcript,
        "summary": state_data.get("summary", ""),
        "keyFacts": [],
        "elapsed": "00:00",
        "aiHandling": not state_data.get("transfer", False),
        "pin": state_data.get("pin", {"lat": 0, "lng": 0}),
        "createdAt": now,
        "updatedAt": now,
    }


def persist_call_at_end(call_id: str, state_data: dict) -> dict | None:
    """
    Write the call to MongoDB once when the call ends (hang_up or transfer).
    Single insert — keeps free-tier Atlas usage minimal.
    """
    doc = _state_to_call_doc(call_id, state_data, datetime.utcnow())
    try:
        calls_collection.insert_one(doc)
        return serialize_call(doc)
    except Exception:
        return None


def parse_transcript(convo: str) -> list:
    """
    Parse transcript string into array of message objects.
    
    Input format: "Dispatcher: Hello\nCaller: Help me\nDispatcher: ..."
    Output format: [{"sender": "ai", "text": "Hello", "time": "..."}, ...]
    """
    messages = []
    lines = convo.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("Dispatcher:"):
            text = line.replace("Dispatcher:", "").strip()
            if text:
                messages.append({
                    "sender": "ai",
                    "text": text,
                    "time": datetime.utcnow().strftime("%H:%M"),
                })
        elif line.startswith("Caller:"):
            text = line.replace("Caller:", "").strip()
            if text:
                messages.append({
                    "sender": "caller",
                    "text": text,
                    "time": datetime.utcnow().strftime("%H:%M"),
                })
    
    return messages
