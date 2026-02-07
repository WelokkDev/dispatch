"""
AI service: Gemini calls for extraction (emergency, location, name, phone)
and generation (next dispatcher line). Option A = few-shot prompts only;
no RAG or fine-tuning. Each prompt is documented with intent and expected output.
"""

import copy
from typing import Optional

import google.generativeai as genai

# Import config so we can switch model in one place.
from config import GEMINI_API_KEY, GEMINI_MODEL

# -----------------------------------------------------------------------------
# Gemini client (lazy init on first use so we don't fail if key is missing at import).
# -----------------------------------------------------------------------------
_model = None


def _get_model():
    """Return configured Gemini model; initializes client on first call."""
    global _model
    if _model is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel(GEMINI_MODEL)
    return _model


# -----------------------------------------------------------------------------
# Few-shot constants (Option A): 2–3 examples per task so the model sees
# real-style inputs/outputs. Teaches "undefined" when caller doesn't provide info.
# -----------------------------------------------------------------------------

# Emergency: short label (under 5 words) for the nature of the emergency.
FEW_SHOT_EMERGENCY = [
    # (convo_snippet, expected_output)
    ("Caller: My dad fell and he's not moving.", "fall, unresponsive person"),
    ("Caller: There's a fire in the kitchen!", "kitchen fire"),
    ("Caller: Someone broke in and I'm hiding.", "break-in, intruder"),
]

# Location: address or place, or "undefined" if not given.
FEW_SHOT_LOCATION = [
    ("Caller: I'm at 123 Main Street.", "123 Main Street"),
    ("Caller: I don't know the address, just near the gas station.", "near gas station"),
    ("Caller: Just send help now! I can't think.", "undefined"),
]

# Name: caller's name or "undefined".
FEW_SHOT_NAME = [
    ("Caller: John Smith.", "John Smith"),
    ("Caller: Just send help please.", "undefined"),
    ("Caller: My name is Maria Garcia.", "Maria Garcia"),
]

# Phone: phone number or "undefined".
FEW_SHOT_PHONE = [
    ("Caller: 555-123-4567.", "555-123-4567"),
    ("Caller: I can't remember right now.", "undefined"),
    ("Caller: It's 416-555-9999.", "416-555-9999"),
]


def extract_emergency(convo: str) -> str:
    """
    Extract the nature of the emergency from the conversation in under 5 words.
    Uses few-shot examples so the model returns a short label (e.g. "fall, unresponsive").
    Returns a stripped string; we do not use "undefined" for emergency (caller always states something).
    """
    # Prompt design: we need a compact label for triage/display; few-shot shows the format.
    few_shot_block = "\n".join(
        f"Conversation: {c}\nEmergency type: {e}" for c, e in FEW_SHOT_EMERGENCY
    )
    prompt = f"""You are a 911 dispatch analyst. Extract only the nature of the emergency from the conversation, in 5 words or fewer.

Examples:
{few_shot_block}

Current conversation:
{convo}

Emergency type (5 words or fewer):"""
    model = _get_model()
    response = model.generate_content(prompt)
    text = (response.text or "").strip()
    return text if text else "emergency"


def extract_location(convo: str) -> str:
    """
    Extract the caller's location/address from the conversation.
    Uses few-shot; returns "undefined" (lowercase) when the caller does not give a location.
    """
    # Prompt design: we need address or place for dispatch; few-shot teaches "undefined" when not provided.
    few_shot_block = "\n".join(
        f"Conversation: {c}\nLocation: {e}" for c, e in FEW_SHOT_LOCATION
    )
    prompt = f"""You are a 911 dispatch analyst. Extract the caller's location or address from the conversation. If the caller does not give any location, respond with exactly: undefined

Examples:
{few_shot_block}

Current conversation:
{convo}

Location (address/place or "undefined"):"""
    model = _get_model()
    response = model.generate_content(prompt)
    text = (response.text or "").strip().lower()
    if "undefined" in text or not text:
        return "undefined"
    return text


def extract_name(convo: str) -> str:
    """
    Extract the caller's name from the conversation.
    Uses few-shot; returns "undefined" when the caller does not give a name.
    """
    few_shot_block = "\n".join(
        f"Conversation: {c}\nName: {e}" for c, e in FEW_SHOT_NAME
    )
    prompt = f"""You are a 911 dispatch analyst. Extract the caller's name from the conversation. If the caller does not give a name, respond with exactly: undefined

Examples:
{few_shot_block}

Current conversation:
{convo}

Name (or "undefined"):"""
    model = _get_model()
    response = model.generate_content(prompt)
    text = (response.text or "").strip()
    if text.lower() == "undefined" or not text:
        return "undefined"
    return text


def extract_phone(convo: str) -> str:
    """
    Extract the caller's phone number from the conversation.
    Uses few-shot; returns "undefined" when the caller does not provide a number.
    """
    few_shot_block = "\n".join(
        f"Conversation: {c}\nPhone: {e}" for c, e in FEW_SHOT_PHONE
    )
    prompt = f"""You are a 911 dispatch analyst. Extract the caller's phone number from the conversation. If the caller does not give a number, respond with exactly: undefined

Examples:
{few_shot_block}

Current conversation:
{convo}

Phone (or "undefined"):"""
    model = _get_model()
    response = model.generate_content(prompt)
    text = (response.text or "").strip().lower()
    if "undefined" in text or not text:
        return "undefined"
    return (response.text or "").strip()


def generate_next_dispatcher_line(
    convo: str, count: int, should_end_call: bool
) -> str:
    """
    Produce the next single dispatcher utterance. Used after we have collected
    emergency, location, name, and number. should_end_call=True means we want
    the model to say help is on the way and end the call (one short line).
    Returns one short line of dialogue; fallback if model returns empty.
    """
    # Branch: count 2 = ask more details + help; count >= 3 or should_end_call = end call; else = more details + safety.
    if should_end_call:
        instruction = """End the call now. Say that help is on the way, you are ending the call to coordinate dispatch, and they will hear back from 911 soon. Write only the next dispatcher line (one short sentence)."""
    elif count == 2:
        instruction = """Ask more detailed questions and provide the caller help in this situation. Do not repeat past lines. Write only the next dispatcher line (one or two short sentences)."""
    else:
        instruction = """Get any more details a dispatcher would need and tell the caller what they can do right now to stay safe until help arrives. Do not repeat anything already mentioned. Write only the next dispatcher line (one or two short sentences)."""

    prompt = f"""You are an automated 911 dispatch officer talking to a caller. Here is the conversation so far:

{convo}

Your job is to create a report for this emergency; a human dispatcher will follow up. Help the caller and give them clear, calm instructions.

{instruction}

Dispatcher:"""
    model = _get_model()
    response = model.generate_content(prompt)
    text = (response.text or "").strip()
    if not text:
        return "Thank you for providing all of this information. A 911 dispatcher will get in contact with you as soon as possible."
    return text
