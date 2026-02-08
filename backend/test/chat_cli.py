"""
Interactive chat CLI for testing the dispatch triage system.
Run from backend/:  python test/chat_cli.py

Type what the caller would say and see the AI's response, urgency, extracted
fields, and status. The conversation continues until the call ends (hang_up
or transfer). Type "quit" to exit, "new" to start a fresh call.

Requires the Flask server to be running:  python app.py
"""

import json
import uuid
import requests

SERVER = "http://localhost:5001"


def chat(call_id: str, message: str) -> dict:
    """Send one caller utterance and return the full result dict."""
    resp = requests.post(
        f"{SERVER}/api/chat",
        json={"call_id": call_id, "message": message},
    )
    resp.raise_for_status()
    return resp.json()


def print_result(result: dict):
    """Pretty-print the triage result after each turn."""
    print()
    print(f"  Dispatcher: {result['spoken_line']}")
    print(f"  ─────────────────────────────────────────")
    print(f"  Urgency:    {result['urgency'] or '—'}")
    print(f"  Emergency:  {result['emergency'] or '—'}")
    print(f"  Location:   {result['location'] or '—'}")
    print(f"  Name:       {result['name'] or '—'}")
    print(f"  Phone:      {result['number'] or '—'}")
    print(f"  Status:     {result['status']}")
    if result["transfer"]:
        print(f"  >>> TRANSFERRED TO OPERATOR <<<")
    if result["hang_up"]:
        print(f"  >>> CALL ENDED <<<")
    print()


def main():
    print("=" * 50)
    print("  911 Dispatch Triage — Chat Test")
    print("=" * 50)
    print()
    print("Commands:")
    print("  Type anything  → send as caller speech")
    print("  new            → start a new call")
    print("  transcript     → show full transcript")
    print("  quit           → exit")
    print()

    call_id = str(uuid.uuid4())[:8]
    last_result = None

    print(f"[Call {call_id} started]")
    print(f"  Dispatcher: 911, what is your emergency?")
    print()

    while True:
        try:
            user_input = input("  Caller: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Exiting.")
            break

        if user_input.lower() == "new":
            call_id = str(uuid.uuid4())[:8]
            last_result = None
            print(f"\n[New call {call_id} started]")
            print(f"  Dispatcher: 911, what is your emergency?")
            print()
            continue

        if user_input.lower() == "transcript" and last_result:
            print("\n--- Full Transcript ---")
            print(last_result["transcript"])
            print("--- End Transcript ---\n")
            continue

        try:
            result = chat(call_id, user_input)
        except requests.ConnectionError:
            print("\n  ERROR: Can't connect to server. Is `python app.py` running?\n")
            continue
        except Exception as e:
            print(f"\n  ERROR: {e}\n")
            continue

        last_result = result
        print_result(result)

        if result["transfer"] or result["hang_up"]:
            outcome = "transferred to operator" if result["transfer"] else "completed"
            print(f"[Call {call_id} ended — {outcome}]")
            print()
            print("  ═══════════════════════════════════════════")
            print("  CALL REPORT")
            print("  ═══════════════════════════════════════════")
            print(f"  Call ID:    {result.get('call_id', call_id)}")
            print(f"  Status:     {result['status']}")
            print(f"  Urgency:    {result['urgency'] or '—'}")
            print(f"  Emergency:  {result['emergency'] or '—'}")
            print(f"  Location:   {result['location'] or '—'}")
            print(f"  Name:       {result['name'] or '—'}")
            print(f"  Phone:      {result['number'] or '—'}")
            print(f"  Transfer:   {result['transfer']}")
            print(f"  Hang up:    {result['hang_up']}")
            print(f"  ─────────────────────────────────────────")
            summary = result.get("summary", "")
            if summary:
                print(f"  Summary:    {summary}")
            else:
                print(f"  Summary:    —")
            print(f"  ─────────────────────────────────────────")
            print(f"  Transcript:")
            for line in result.get("transcript", "").strip().split("\n"):
                line = line.strip()
                if line:
                    print(f"    {line}")
            print(f"  ═══════════════════════════════════════════")
            print()
            print(f"[Type 'new' for a new call or 'quit' to exit]\n")


if __name__ == "__main__":
    main()
