"""
Test script for calls API (POST /api/calls, GET /api/calls).
Run from backend/:  python test/test_calls_api.py
Requires MONGODB_URI in .env (uses real DB; creates one document per run).
"""

import sys
import os

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


def main():
    print("=== Calls API test ===\n")
    test_post_requires_number_masked()
    test_post_create_call()
    #test_get_calls()
    print("\n=== Done ===")


if __name__ == "__main__":
    main()


