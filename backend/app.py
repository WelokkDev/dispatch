import os
import uuid
from datetime import datetime
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
"""
Dispatch backend: Flask app, health/api routes, and call handling.
Twilio routes (e.g. POST /voice/incoming, POST /voice/respond) will be added here
and will use handle_caller_speech(call_id, voice_input) to get the next line and hang_up flag.
"""

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS

from services.triage import CallState, generate_ai_response

app = Flask(__name__)

# Mock database to store call metadata
call_logs = {}

def mask_number(phone_number):
    """Masks the caller ID, showing only the last 4 digits."""
    if not phone_number:
        return "Unknown"
    return f"XXX-XXX-{phone_number[-4:]}"

@app.route("/voice", methods=['POST'])
def voice_intake():
    """Handle incoming 911-style demo calls."""
    
    # 1. Generate Unique Session ID
    session_id = str(uuid.uuid4())
    
    # 2. Capture Metadata
    raw_caller = request.values.get('From', '')
    call_sid = request.values.get('CallSid', '') # Twilio's internal ID
    timestamp = datetime.utcnow().isoformat()
    
    # 3. Process/Mask Data
    masked_caller = mask_number(raw_caller)
    
    # Store in logs (In production, use a DB like PostgreSQL or Redis)
    call_logs[session_id] = {
        "call_sid": call_sid,
        "timestamp": timestamp,
        "caller": masked_caller,
        "status": "in-progress"
    }

    # 4. Generate Twilio Response (TwiML)
    response = VoiceResponse()
    response.say("Emergency dispatch demo. This call is being recorded and processed.", 
                 voice='polly.Amy')
    
    # Example: Start a recording or gather input
    # response.record(max_length=30, action='/handle-recording')

    print(f"Log Created: {call_logs[session_id]}")
    
    return str(response)
# Maps call_id (e.g. Twilio CallSid) to CallState. In production use Redis or a session store.
call_states: dict[str, CallState] = {}


def handle_caller_speech(call_id: str, voice_input: str) -> dict:
    """
    Process one caller utterance and return a dict with everything the Twilio
    handler and the frontend need.

    Returns:
        {
            "spoken_line": str,   # What the AI says back to the caller
            "hang_up": bool,      # True = end the call
            "transfer": bool,     # True = transfer to human operator (P0/P1)
            "urgency": str|None,  # Current urgency: P0, P1, P2, P3
            "emergency": str|None,# Emergency type extracted so far
            "location": str|None, # Location extracted so far
            "name": str|None,     # Caller name extracted so far
            "number": str|None,   # Phone number extracted so far
            "transcript": str,    # Full conversation transcript
            "call_id": str,       # The call identifier
            "status": str,        # "in_progress", "transferred", or "completed"
        }
    """
    if call_id not in call_states:
        # New call: initial state with first dispatcher line in transcript.
        call_states[call_id] = CallState(convo="Dispatcher: 911, what is your emergency?\n")
    state = call_states[call_id]

    # generate_ai_response now returns 4 values: (state, spoken_line, hang_up, transfer)
    state, spoken_line, hang_up, transfer = generate_ai_response(state, voice_input)
    call_states[call_id] = state

    # Determine call status for the frontend.
    if transfer:
        status = "transferred"
    elif hang_up:
        status = "completed"
    else:
        status = "in_progress"

    # Return all data the frontend/Twilio handler needs.
    return {
        "spoken_line": spoken_line,
        "hang_up": hang_up,
        "transfer": transfer,
        "urgency": state.urgency,
        "emergency": state.emergency,
        "location": state.location,
        "name": state.name,
        "number": state.number,
        "transcript": state.convo,
        "call_id": call_id,
        "status": status,
    }


# =============================================================================
# Text-based test endpoint: simulate a call via REST instead of Twilio voice.
# POST /api/chat with JSON: {"call_id": "test-1", "message": "My house is on fire!"}
# Returns the same dict handle_caller_speech returns so you can see urgency,
# extraction, transcript, transfer, etc. Use any HTTP client (curl, Postman,
# or the frontend) to test the full triage flow without a phone call.
# =============================================================================

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Text-based test route. Simulates one caller utterance per request.
    Send JSON: {"call_id": "any-string", "message": "what the caller says"}
    Returns the full triage result (spoken_line, urgency, fields, transcript, etc.)
    Use the same call_id across requests to continue the same "call".
    """
    data = request.get_json(force=True)
    call_id = data.get("call_id")
    message = data.get("message")

    if not call_id or not message:
        return jsonify({"error": "call_id and message are required"}), 400

    result = handle_caller_speech(call_id, message)
    return jsonify(result)


@app.route("/api/calls", methods=["GET"])
def get_calls():
    """
    Return all active call states. Useful for the frontend dashboard to see
    every call's urgency, fields, transcript, and status at a glance.
    """
    calls = []
    for cid, state in call_states.items():
        calls.append({
            "call_id": cid,
            "urgency": state.urgency,
            "emergency": state.emergency,
            "location": state.location,
            "name": state.name,
            "number": state.number,
            "transfer": state.transfer,
            "transcript": state.convo,
            "status": "transferred" if state.transfer else "in_progress",
        })
    return jsonify(calls)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Backend connected"})


@app.route("/api")
def index():
    return jsonify({"message": "Dispatch API"})


if __name__ == "__main__":
    app.run(port=5001, debug=True)