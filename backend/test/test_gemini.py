"""
Test script for Gemini (services.ai) only.
Run from backend/:  python test_gemini.py
Requires GEMINI_API_KEY in .env.
"""

from dotenv import load_dotenv
load_dotenv()

from services.ai import (
    extract_emergency,
    extract_location,
    extract_name,
    extract_phone,
    generate_next_dispatcher_line,
)


def main():
    print("=== Gemini AI service test ===\n")

    # --- Extract emergency ---
    convo_emergency = """Dispatcher: 911, what is your emergency?
Caller: My husband collapsed and he's not breathing.
Dispatcher: """
    out = extract_emergency(convo_emergency)
    print("1. extract_emergency:")
    print(f"   Convo: ...{convo_emergency.strip()[-60:]}")
    print(f"   -> {out!r}\n")

    # --- Extract location ---
    convo_location = """Dispatcher: 911, what is your emergency?
Caller: There's a fire!
Dispatcher: Okay, stay calm. Can you tell me your location?
Caller: I'm at 456 Oak Avenue, apartment 3B.
Dispatcher: """
    out = extract_location(convo_location)
    print("2. extract_location:")
    print(f"   Convo: ...(caller said 456 Oak Avenue, apt 3B)")
    print(f"   -> {out!r}\n")

    # --- Extract name ---
    convo_name = """...Caller: My name is Sarah Chen.
Dispatcher: """
    out = extract_name(convo_name)
    print("3. extract_name:")
    print(f"   Convo: ...Sarah Chen")
    print(f"   -> {out!r}\n")

    # --- Extract phone ---
    convo_phone = """...Caller: 555-987-6543.
Dispatcher: """
    out = extract_phone(convo_phone)
    print("4. extract_phone:")
    print(f"   Convo: ...555-987-6543")
    print(f"   -> {out!r}\n")

    # --- Generate next dispatcher line (more details) ---
    convo_full = """Dispatcher: 911, what is your emergency?
Caller: My dad fell and he's not moving.
Dispatcher: Okay, stay calm. Can you tell me your location?
Caller: 123 Main Street.
Dispatcher: Okay, can I get your full name?
Caller: Jane Doe.
Dispatcher: And what's your phone number just in case we're disconnected?
Caller: 555-123-4567.
Dispatcher: """
    line = generate_next_dispatcher_line(convo_full, count=1, should_end_call=False)
    print("5. generate_next_dispatcher_line (count=1, more details):")
    print(f"   -> {line!r}\n")

    # --- Generate next dispatcher line (end call) ---
    line_end = generate_next_dispatcher_line(convo_full + "Stay with him, help is on the way.\nDispatcher: ", count=3, should_end_call=True)
    print("6. generate_next_dispatcher_line (count=3, end call):")
    print(f"   -> {line_end!r}\n")

    print("=== Done ===")


if __name__ == "__main__":
    main()
