"""
Send a longer /api/chat conversation to a running backend so you can see
the call and transcript appear in the dashboard in real time (4+ back-and-forth).

Usage:
  1. Start backend:  python app.py
  2. Start frontend and open the dashboard in a browser
  3. Run:  python test/run_live_demo.py

Requires: requests, and backend running at http://127.0.0.1:5001
"""

import sys
import time
import uuid

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

BASE = "http://127.0.0.1:5001"
call_id = f"demo-{uuid.uuid4().hex[:8]}"

# P2-style flow: emergency → location → name → phone → a couple of dispatcher lines (4+ turns)
messages = [
    "There's been a car accident at 123 Main Street. Two cars.",
    "123 Main Street, near the gas station.",
    "My name is Jane Doe.",
    "555-123-4567.",
    "Yes, I can stay on the line.",
]

def main():
    print(f"Call ID: {call_id}")
    print(f"Sending {len(messages)} messages to {BASE}/api/chat (watch the dashboard).\n")
    for i, msg in enumerate(messages):
        print(f"  [{i+1}] Caller: {msg[:55]}{'...' if len(msg) > 55 else ''}")
        try:
            r = requests.post(
                f"{BASE}/api/chat",
                json={"call_id": call_id, "message": msg},
                timeout=90,
            )
            r.raise_for_status()
            data = r.json()
            spoken = (data.get("spoken_line") or "")[:65]
            print(f"      AI:  {spoken}{'...' if len(data.get('spoken_line') or '') > 65 else ''}")
            if data.get("transfer") or data.get("hang_up"):
                print("      [Call ended]")
                break
        except requests.exceptions.RequestException as e:
            print(f"      Error: {e}")
            sys.exit(1)
        # Pause so the UI can show each exchange before the next
        time.sleep(1.2)
    print("\nDone. Check the dashboard for the full call and transcript.")


if __name__ == "__main__":
    main()
