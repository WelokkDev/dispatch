"""
Send a short /api/chat conversation to a running backend so you can see
the call and transcript appear in the dashboard in real time.

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

messages = [
    "My husband collapsed and he's not breathing. We're at 456 Oak Avenue.",
    "He's not moving.",
]

def main():
    print(f"Call ID: {call_id}")
    print(f"Opening dashboard and sending {len(messages)} messages to {BASE}/api/chat ...\n")
    for i, msg in enumerate(messages):
        print(f"  [{i+1}] Caller: {msg[:50]}...")
        try:
            r = requests.post(
                f"{BASE}/api/chat",
                json={"call_id": call_id, "message": msg},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            print(f"      AI: {data.get('spoken_line', '')[:60]}...")
            if data.get("transfer") or data.get("hang_up"):
                print("      [Call ended]")
                break
        except requests.exceptions.RequestException as e:
            print(f"      Error: {e}")
            sys.exit(1)
        time.sleep(0.5)
    print("\nDone. Check the dashboard for the live call and transcript.")

if __name__ == "__main__":
    main()
