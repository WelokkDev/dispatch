"""
Dispatch backend: Flask app with Twilio voice integration and Gradium TTS.

Voice flow (turn-based):
  1. Caller dials Twilio number → Twilio POSTs to /voice
  2. We generate a greeting via Gradium TTS, respond with <Gather> + <Play>
  3. Caller speaks → Twilio transcribes (built-in STT) → POSTs to /voice/respond
  4. We run triage (Gemini), generate response audio (Gradium TTS), loop
  5. On hang_up or transfer the call ends or is forwarded.

Text-based /api/chat endpoint is kept for testing without a phone.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather

from dotenv import load_dotenv
load_dotenv()

from flask_cors import CORS

from services.triage import CallState, generate_ai_response
from services.voice import generate_audio, AUDIO_DIR
from routes.calls import calls_bp
from db import persist_call_at_end



app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(calls_bp)


# ═══════════════════════════════════════════════════════════════════════════════
# In-memory call state (same as before — maps CallSid → CallState)
# ═══════════════════════════════════════════════════════════════════════════════

call_states: dict[str, CallState] = {}


def handle_caller_speech(call_id: str, voice_input: str) -> dict:
    """
    Process one caller utterance and return a dict with everything the Twilio
    handler and the frontend need.
    """
    if call_id not in call_states:
        call_states[call_id] = CallState(convo="Dispatcher: 911, what is your emergency?\n")
    state = call_states[call_id]

    state, spoken_line, hang_up, transfer = generate_ai_response(state, voice_input)
    call_states[call_id] = state

    if transfer:
        status = "transferred"
    elif hang_up:
        status = "completed"
    else:
        status = "in_progress"

    result = {
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
    if result["hang_up"] or result["transfer"]:
        persist_call_at_end(call_id, result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Serve generated audio files so Twilio can <Play> them via the ngrok URL
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/audio/<filename>")
def serve_audio(filename):
    """Serve a generated WAV file. Twilio fetches this URL for <Play>."""
    return send_from_directory(AUDIO_DIR, filename, mimetype="audio/wav")


# ═══════════════════════════════════════════════════════════════════════════════
# Twilio voice webhooks
# ═══════════════════════════════════════════════════════════════════════════════

GREETING_TEXT = "911, what is your emergency?"


@app.route("/voice", methods=["POST"])
def voice_incoming():
    """
    Twilio hits this when someone calls your number.
    We generate the greeting audio via Gradium TTS, then ask Twilio to play
    it and listen for the caller's speech.
    """
    call_sid = request.form.get("CallSid", "unknown")
    caller = request.form.get("From", "unknown")
    print(f"[Twilio] Incoming call {call_sid} from {caller}")

    # Generate greeting audio via Gradium TTS
    audio_file = generate_audio(GREETING_TEXT, label="greeting")
    audio_url = f"{request.url_root}audio/{audio_file}"

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/voice/respond",
        method="POST",
        speech_timeout="auto",
        language="en-US",
    )
    gather.play(audio_url)
    response.append(gather)

    # Fallback if caller says nothing — repeat the greeting
    response.redirect("/voice", method="POST")

    print(f"[Twilio] Responding with greeting: {audio_url}")
    return str(response), 200, {"Content-Type": "text/xml"}


@app.route("/voice/respond", methods=["POST"])
def voice_respond():
    """
    Twilio hits this after <Gather> captures the caller's speech.
    We run the triage pipeline and respond with the next dispatcher line.
    """
    call_sid = request.form.get("CallSid", "unknown")
    speech_result = request.form.get("SpeechResult", "")
    confidence = request.form.get("Confidence", "?")

    print(f"[Twilio] CallSid={call_sid}  Speech=\"{speech_result}\"  Confidence={confidence}")

    if not speech_result:
        # No speech detected — ask again
        response = VoiceResponse()
        response.say("I didn't catch that. Can you repeat?")
        response.redirect("/voice", method="POST")
        return str(response), 200, {"Content-Type": "text/xml"}

    # Run the triage pipeline
    result = handle_caller_speech(call_sid, speech_result)
    spoken_line = result["spoken_line"]
    hang_up = result["hang_up"]
    transfer = result["transfer"]

    print(f"[Triage] urgency={result['urgency']}  hang_up={hang_up}  transfer={transfer}")
    print(f"[Triage] spoken_line: {spoken_line}")

    # Generate response audio via Gradium TTS
    audio_file = generate_audio(spoken_line, label="dispatch")
    audio_url = f"{request.url_root}audio/{audio_file}"

    response = VoiceResponse()

    if hang_up:
        # Final line, then hang up
        response.play(audio_url)
        response.hangup()

    elif transfer:
        # Play the transfer message, then end (in production you'd <Dial> an operator)
        response.play(audio_url)
        response.say("Transferring you now. Please stay on the line.")
        # Uncomment and set a real operator number to actually transfer:
        # response.dial("+1XXXXXXXXXX")
        response.hangup()

    else:
        # Normal turn — play response, then gather next speech
        gather = Gather(
            input="speech",
            action="/voice/respond",
            method="POST",
            speech_timeout="auto",
            language="en-US",
        )
        gather.play(audio_url)
        response.append(gather)
        # Fallback if no speech
        response.redirect("/voice", method="POST")

    return str(response), 200, {"Content-Type": "text/xml"}


# ═══════════════════════════════════════════════════════════════════════════════
# Text-based test endpoint (unchanged — for testing without a phone)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Text-based test route. Simulates one caller utterance per request.
    Send JSON: {"call_id": "any-string", "message": "what the caller says"}
    """
    data = request.get_json(force=True)
    call_id = data.get("call_id")
    message = data.get("message")

    if not call_id or not message:
        return jsonify({"error": "call_id and message are required"}), 400

    result = handle_caller_speech(call_id, message)
    return jsonify(result)


@app.route("/api/active-calls", methods=["GET"])
def get_active_calls():
    """
    Return all active in-memory call states. This shows the raw triage
    state for calls currently being handled by the AI.
    Note: /api/calls (Blueprint) returns persisted MongoDB data for the dashboard.
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
    print("=" * 60)
    print("  Dispatch backend starting on http://localhost:5001")
    print("  Make sure ngrok is running:  ngrok http 5001")
    print("  Then set Twilio webhook to:  https://<ngrok-url>/voice")
    print("=" * 60)
    app.run(port=5001, debug=True)
