import os
import uuid
from datetime import datetime
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

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

if __name__ == "__main__":
    app.run(port=5001, debug=True)