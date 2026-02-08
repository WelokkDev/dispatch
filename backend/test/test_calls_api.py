"""
Test script for calls API (POST /api/calls, GET /api/calls).
Run from backend/:  python test/test_calls_api.py
Requires MONGODB_URI in .env. E2E test also needs GEMINI_API_KEY and full app (no sock errors).
"""

import sys
import os
import uuid

# Run from backend/ so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import app


def test_post_create_call():
    """POST /api/calls with numberMasked returns 201 and the created call."""
    with app.test_client() as client:
        r = client.post(
            "/api/calls",
            json={"numberMasked": "XXX-XXX-1234"},
            content_type="application/json",
        )
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.data}"
        data = r.get_json()
        assert "id" in data
        assert data.get("numberMasked") == "XXX-XXX-1234"
        assert data.get("priority") == "P4"
        assert data.get("status") == "AI handling"
        assert "pin" in data and data["pin"].get("lat") == 0
        print("POST /api/calls: OK — created call id:", data["id"])


def test_post_requires_number_masked():
    """POST /api/calls without numberMasked returns 400."""
    with app.test_client() as client:
        r = client.post("/api/calls", json={}, content_type="application/json")
        assert r.status_code == 400
        assert b"numberMasked" in r.data or "numberMasked" in r.get_json().get("error", "")
    print("POST /api/calls (missing numberMasked): OK — 400")


def test_get_calls():
    """GET /api/calls returns 200 and a list (may be empty)."""
    with app.test_client() as client:
        r = client.get("/api/calls")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        print("GET /api/calls: OK — list length:", len(data))


def test_e2e_full_call_persisted_with_transcript():
    """
    End-to-end: simulate a full call via /api/chat until hang_up or transfer,
    then assert the call is in MongoDB with non-empty transcript (conversation logs).
    """
    call_id = f"e2e-{uuid.uuid4().hex[:12]}"
    # High-urgency scenario so the flow ends in 1–3 turns (transfer or hang_up)
    messages = [
        "My husband collapsed and he's not breathing. We're at 456 Oak Avenue.",
        "He's not moving.",
    ]
    max_turns = 8
    ended = False

    with app.test_client() as client:
        for i, msg in enumerate(messages):
            if i >= max_turns:
                break
            r = client.post(
                "/api/chat",
                json={"call_id": call_id, "message": msg},
                content_type="application/json",
            )
            assert r.status_code == 200, f"chat returned {r.status_code}: {r.data}"
            result = r.get_json()
            assert "hang_up" in result and "transfer" in result
            if result["hang_up"] or result["transfer"]:
                ended = True
                break

        assert ended, "Call did not end (hang_up or transfer) within max_turns"

        # Persisted call should be in MongoDB (persist_call_at_end was called)
        r = client.get(f"/api/calls/{call_id}")
        if r.status_code == 404:
            # Try finding by id in list (id might be stored as call_id in payload)
            r = client.get("/api/calls")
            assert r.status_code == 200
            calls = r.get_json()
            call = next((c for c in calls if c.get("id") == call_id), None)
            assert call is not None, f"Call {call_id} not found in GET /api/calls"
        else:
            assert r.status_code == 200
            call = r.get_json()

        # Must have transcript as a list with conversation
        transcript = call.get("transcript") or []
        assert isinstance(transcript, list), "transcript should be a list"
        assert len(transcript) > 0, "transcript should not be empty (conversation logs)"
        has_caller = any(m.get("sender") == "caller" for m in transcript)
        has_ai = any(m.get("sender") == "ai" for m in transcript)
        assert has_caller and has_ai, "transcript should contain both caller and ai messages"

        print("E2E: OK — full call persisted with transcript length:", len(transcript))
        print("     status:", call.get("status"), " priority:", call.get("priority"))


def main():
    print("=== Calls API test ===\n")
    test_post_requires_number_masked()
    test_post_create_call()
    test_get_calls()
    test_e2e_full_call_persisted_with_transcript()
    print("\n=== Done ===")


if __name__ == "__main__":
    main()


