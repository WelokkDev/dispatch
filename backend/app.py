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


def handle_caller_speech(call_id: str, voice_input: str) -> tuple[str, bool]:
    """
    Process one caller utterance and return (spoken_line, hang_up).
    Twilio /voice/respond handler should call this with CallSid and SpeechResult,
    then speak spoken_line and hang up if hang_up is True.
    If this is the first time we see call_id, we create initial state with the
    first dispatcher line already in convo ("911, what is your emergency?").
    """
    if call_id not in call_states:
        # New call: initial state with first dispatcher line in transcript.
        call_states[call_id] = CallState(convo="Dispatcher: 911, what is your emergency?\n")
    state = call_states[call_id]
    state, spoken_line, hang_up = generate_ai_response(state, voice_input)
    call_states[call_id] = state
    return spoken_line, hang_up


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Backend connected"})


@app.route("/api")
def index():
    return jsonify({"message": "Dispatch API"})


if __name__ == "__main__":
    app.run(port=5001, debug=True)