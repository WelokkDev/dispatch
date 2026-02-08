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

import json
import os
import queue
import time
import threading
import requests as http_requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from dotenv import load_dotenv
load_dotenv()

from flask_cors import CORS

from services.triage import CallState, generate_ai_response
from services.ai import generate_incident_summary
from services.voice import generate_audio, precache_fixed_lines, AUDIO_DIR
from routes.calls import calls_bp
from db import persist_call_at_end, parse_transcript
from events import broadcast, subscribe, unsubscribe



# ═══════════════════════════════════════════════════════════════════════════════
# Geocoding: convert text address → lat/lng via OpenStreetMap Nominatim (free)
# ═══════════════════════════════════════════════════════════════════════════════
_geocode_cache: dict[str, dict] = {}

NO_PIN = {"lat": 0, "lng": 0}  # No location yet — frontend hides (0,0) markers

def geocode_location(address: str) -> tuple[dict, int]:
    """
    Convert a text address to ({"lat": ..., "lng": ...}, confidence_pct) using Nominatim.
    Results are cached in memory so repeated lookups are instant.
    Returns (NO_PIN, 0) as fallback if geocoding fails or address is invalid.
    Confidence is derived from Nominatim's 'importance' field (0-1 → 0-100%).
    """
    if not address or address.lower() in ("undefined", "unknown"):
        return NO_PIN, 0

    # Check cache first
    cache_key = address.strip().lower()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        resp = http_requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{address}, Kingston, Ontario, Canada",
                "format": "json",
                "limit": 1,
            },
            headers={"User-Agent": "dispatch-911-hackathon/1.0"},
            timeout=3,
        )
        results = resp.json()
        if results:
            hit = results[0]
            pin = {"lat": float(hit["lat"]), "lng": float(hit["lon"])}
            # Nominatim 'importance' is 0-1; convert to 0-100 percentage
            importance = float(hit.get("importance", 0.5))
            confidence = min(100, max(0, round(importance * 100)))
            _geocode_cache[cache_key] = (pin, confidence)
            print(f"[Geocode] '{address}' → {pin['lat']:.4f}, {pin['lng']:.4f} ({confidence}% confidence)")
            return pin, confidence
    except Exception as e:
        print(f"[Geocode] Failed for '{address}': {e}")

    _geocode_cache[cache_key] = (NO_PIN, 0)
    return NO_PIN, 0


app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(calls_bp)


# ═══════════════════════════════════════════════════════════════════════════════
# Global error handler — Twilio must ALWAYS get valid TwiML, never a 500
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(Exception)
def handle_any_error(e):
    """Last-resort safety net. If ANY route throws, log it and return safe TwiML
    for Twilio paths or a JSON error for API paths."""
    import traceback
    print(f"[GLOBAL ERROR] {type(e).__name__}: {e}")
    traceback.print_exc()

    path = request.path or ""
    if path.startswith("/voice"):
        # Twilio route — must return valid TwiML
        response = VoiceResponse()
        response.say("We are experiencing a temporary issue. Please hold.")
        response.redirect("/voice", method="POST")
        return str(response), 200, {"Content-Type": "text/xml"}

    # API route — return JSON error
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════════
# In-memory call state (same as before — maps CallSid → CallState)
# ═══════════════════════════════════════════════════════════════════════════════

call_states: dict[str, CallState] = {}


def _urgency_to_priority(urgency: str) -> str:
    m = {"P0": "P1", "P1": "P2", "P2": "P3", "P3": "P4"}
    return m.get(urgency, "P4")


def _live_stub(call_id: str, number: str = None) -> dict:
    """Build a minimal call dict for SSE (frontend shape, JSON-safe)."""
    return {
        "id": call_id,
        "numberMasked": (number and str(number).strip()) or "Unknown",
        "priority": "P4",
        "incidentType": "",
        "incidentIcon": "",
        "status": "AI handling",
        "statusDetail": "",
        "locationLabel": "",
        "address": "",
        "city": "",
        "confidence": 0,
        "inServiceArea": True,
        "transcript": [],
        "summary": "",
        "keyFacts": [],
        "elapsed": "00:00",
        "aiHandling": True,
        "pin": NO_PIN,
    }


def handle_caller_speech(call_id: str, voice_input: str, caller_phone: str = None) -> dict:
    """
    Process one caller utterance and return a dict with everything the Twilio
    handler and the frontend need.
    caller_phone: optional; from Twilio request.form.get("From") so we show real number.
    """
    is_new = call_id not in call_states
    if is_new:
        call_states[call_id] = CallState(convo="Dispatcher: 911, what is your emergency?\n")
        stub = _live_stub(call_id, caller_phone)
        broadcast({"type": "call_created", "call": stub})

    state = call_states[call_id]

    # Push caller message first so the UI can show it before the AI reply
    broadcast({
        "type": "new_message",
        "call_id": call_id,
        "message": {"sender": "caller", "text": voice_input, "time": datetime.utcnow().strftime("%H:%M")},
    })

    state, spoken_line, hang_up, transfer = generate_ai_response(state, voice_input)
    call_states[call_id] = state

    if transfer:
        status = "transferred"
    elif hang_up:
        status = "completed"
    else:
        status = "in_progress"

    # Geocode the location to get real map coordinates + confidence
    location_text = (state.location or "").replace("undefined", "")
    pin, geo_confidence = geocode_location(location_text) if location_text else (NO_PIN, 0)

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
        "pin": pin,
        "confidence": geo_confidence,
    }

    transcript_list = parse_transcript(state.convo)
    status_display = "AI → Human Takeover" if transfer else ("Completed" if hang_up else "AI handling")
    broadcast({
        "type": "transcript_update",
        "call_id": call_id,
        "transcript": transcript_list,
        "status": status_display,
        "aiHandling": not (hang_up or transfer),
        "priority": _urgency_to_priority(state.urgency),
        "incidentType": (state.emergency or "").replace("undefined", ""),
        "locationLabel": location_text,
        "pin": pin,
        "confidence": geo_confidence,
    })

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
            # Push summary to frontend once it's ready
            broadcast({
                "type": "summary_update",
                "call_id": call_id,
                "summary": summary,
            })
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
    NEVER returns 500 — always gives the caller valid TwiML.
    """
    try:
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

    except Exception as e:
        # SAFETY NET: if anything fails, use Twilio's built-in <Say> so the
        # caller still hears a greeting instead of "application error".
        print(f"[voice_incoming ERROR] {type(e).__name__}: {e}")
        response = VoiceResponse()
        gather = Gather(
            input="speech",
            action="/voice/respond",
            method="POST",
            speech_timeout="2",
            language="en-US",
        )
        gather.say("911, what is your emergency?")
        response.append(gather)
        response.redirect("/voice", method="POST")
        return str(response), 200, {"Content-Type": "text/xml"}


@app.route("/voice/respond", methods=["POST"])
def voice_respond():
    """
    Twilio hits this after <Gather> captures the caller's speech.
    We run the triage pipeline and respond with the next dispatcher line.
    NEVER returns 500 — always gives the caller valid TwiML.
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

    try:
        # Run the triage pipeline (Gemini calls). Pass Twilio From so we show real number.
        caller_phone = request.form.get("From")
        t0 = time.time()
        result = handle_caller_speech(call_sid, speech_result, caller_phone=caller_phone)
        t_triage = time.time() - t0

        spoken_line = result["spoken_line"]
        hang_up = result["hang_up"]
        transfer = result["transfer"]

        print(f"[Triage] urgency={result['urgency']}  hang_up={hang_up}  transfer={transfer}  ({t_triage:.1f}s)")
        print(f"[Triage] spoken_line: {spoken_line}")

        # Generate response audio via Gradium TTS.
        # If Gradium fails (cache miss + API down), fall back to Twilio <Say>.
        audio_url = None
        try:
            t1 = time.time()
            audio_file = generate_audio(spoken_line, label="dispatch")
            t_tts = time.time() - t1
            audio_url = f"{request.url_root}audio/{audio_file}"
            print(f"[Timing] triage={t_triage:.1f}s  tts={t_tts:.1f}s  total={t_triage + t_tts:.1f}s")
        except Exception as e:
            print(f"[Gradium ERROR] TTS failed, using <Say> fallback: {e}")

        response = VoiceResponse()

        if hang_up:
            if audio_url:
                response.play(audio_url)
            else:
                response.say(spoken_line)
            response.hangup()

        elif transfer:
            if audio_url:
                response.play(audio_url)
            else:
                response.say(spoken_line)
            # Transfer message
            try:
                transfer_msg = "Transferring you now. Please stay on the line."
                transfer_file = generate_audio(transfer_msg, label="transfer")
                transfer_url = f"{request.url_root}audio/{transfer_file}"
                response.play(transfer_url)
            except Exception:
                response.say("Transferring you now. Please stay on the line.")
            response.hangup()

        else:
            gather = Gather(
                input="speech",
                action="/voice/respond",
                method="POST",
                speech_timeout="2",
                language="en-US",
            )
            if audio_url:
                gather.play(audio_url)
            else:
                gather.say(spoken_line)
            response.append(gather)
            response.redirect("/voice", method="POST")

        return str(response), 200, {"Content-Type": "text/xml"}

    except Exception as e:
        # SAFETY NET: if triage or anything else explodes, don't kill the call.
        # Ask the caller to repeat — this gives the system another chance.
        print(f"[voice_respond CRITICAL ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("I'm sorry, could you repeat that?")
        response.redirect("/voice", method="POST")
        return str(response), 200, {"Content-Type": "text/xml"}


# ═══════════════════════════════════════════════════════════════════════════════
# Text-based test endpoint (unchanged — for testing without a phone)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/events")
def events():
    """Server-Sent Events: real-time call_created and transcript_update."""
    def gen():
        q = subscribe()
        try:
            while True:
                try:
                    event = q.get(timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            unsubscribe(q)

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


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
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Helpful startup banner (optional)
    if debug:
        print("=" * 60)
        print(f"  [Dev] Dispatch backend starting on http://localhost:{port}")
        print("  (If using Twilio locally, use ngrok and point webhooks to /voice)")
        print("=" * 60)
    else:
        print("=" * 60)
        print(f"  Dispatch backend starting on http://0.0.0.0:{port}")
        print("=" * 60)

    # ✅ Pre-cache once (avoid double-run when debug reloader is on)
    should_precache = (not debug) or (os.environ.get("WERKZEUG_RUN_MAIN") == "true")
    if should_precache:
        precache_fixed_lines()

    # ✅ Correct binding for Render / Railway
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=debug,  # reloader only in dev
    )

