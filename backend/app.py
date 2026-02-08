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
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather

from dotenv import load_dotenv
load_dotenv()

from flask_cors import CORS

from services.triage import CallState, generate_ai_response
from services.ai import generate_incident_summary
from services.voice import generate_audio, precache_fixed_lines, AUDIO_DIR
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
        "summary": "",
    }

    # Generate summary + persist to DB in background so we don't block the response.
    # The caller hears the final line immediately instead of waiting.
    if hang_up or transfer:
        def _finalize():
            summary = generate_incident_summary(
                convo=state.convo,
                emergency=state.emergency or "",
                location=state.location or "",
                urgency=state.urgency or "",
            )
            print(f"[Summary] {summary}")
            result["summary"] = summary
            persist_call_at_end(call_id, result)
        threading.Thread(target=_finalize, daemon=True).start()

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
    Plays the pre-cached greeting, then listens for caller speech.
    """
    call_sid = request.form.get("CallSid", "unknown")
    caller = request.form.get("From", "unknown")
    print(f"[Twilio] Incoming call {call_sid} from {caller}")

    # generate_audio() returns instantly from cache for fixed lines.
    audio_file = generate_audio(GREETING_TEXT, label="greeting")
    audio_url = f"{request.url_root}audio/{audio_file}"

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/voice/respond",
        method="POST",
        speech_timeout="2",
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

    # Reject empty or low-confidence speech (background noise, echo, etc.)
    try:
        conf = float(confidence)
    except (ValueError, TypeError):
        conf = 0.0

    if not speech_result or conf < 0.4:
        print(f"[Twilio] Ignored — empty or low confidence ({conf:.2f}). Re-prompting.")
        response = VoiceResponse()
        response.redirect("/voice", method="POST")
        return str(response), 200, {"Content-Type": "text/xml"}

    # Run the triage pipeline (Gemini calls)
    t0 = time.time()
    result = handle_caller_speech(call_sid, speech_result)
    t_triage = time.time() - t0

    spoken_line = result["spoken_line"]
    hang_up = result["hang_up"]
    transfer = result["transfer"]

    print(f"[Triage] urgency={result['urgency']}  hang_up={hang_up}  transfer={transfer}  ({t_triage:.1f}s)")
    print(f"[Triage] spoken_line: {spoken_line}")

    # Generate response audio via Gradium TTS
    t1 = time.time()
    audio_file = generate_audio(spoken_line, label="dispatch")
    t_tts = time.time() - t1

    audio_url = f"{request.url_root}audio/{audio_file}"
    print(f"[Timing] triage={t_triage:.1f}s  tts={t_tts:.1f}s  total={t_triage + t_tts:.1f}s")

    response = VoiceResponse()

    if hang_up:
        response.play(audio_url)
        response.hangup()

    elif transfer:
        response.play(audio_url)
        # Use cached Gradium audio instead of Twilio's robotic <Say>.
        transfer_msg = "Transferring you now. Please stay on the line."
        transfer_file = generate_audio(transfer_msg, label="transfer")
        transfer_url = f"{request.url_root}audio/{transfer_file}"
        response.play(transfer_url)
        response.hangup()

    else:
        gather = Gather(
            input="speech",
            action="/voice/respond",
            method="POST",
            speech_timeout="2",
            language="en-US",
        )
        gather.play(audio_url)
        response.append(gather)
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

    # Pre-cache all fixed dispatcher lines so calls get instant TTS responses.
    # This runs once at startup (~15-20s) and eliminates TTS latency for ~90% of turns.
    # The WERKZEUG_RUN_MAIN check avoids double-caching when Flask's debug reloader is active.
    import os as _os
    if _os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        precache_fixed_lines()

    app.run(port=5001, debug=True)
