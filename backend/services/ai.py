"""
AI service: Gemini calls for extraction (emergency, location, name, phone)
and generation (next dispatcher line). Option A = few-shot prompts only;
no RAG or fine-tuning. Each prompt is documented with intent and expected output.
Uses the google-genai SDK (client.models.generate_content).
"""

from google import genai

# Import config so we can switch model in one place.
from config import GEMINI_API_KEY, GEMINI_MODEL

# -----------------------------------------------------------------------------
# Gemini client (lazy init on first use so we don't fail if key is missing at import).
# -----------------------------------------------------------------------------
_client = None


def _get_client():
    """Return configured Gemini client; initializes on first call."""
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


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
    client = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
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
    client = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
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
    client = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
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
    client = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    text = (response.text or "").strip().lower()
    if "undefined" in text or not text:
        return "undefined"
    return (response.text or "").strip()


# -----------------------------------------------------------------------------
# Urgency assessment: called EVERY turn before any extraction or generation.
# Returns one of P0, P1, P2, P3 based on the full conversation so far.
# Urgency can escalate (or de-escalate) as the caller reveals more.
# -----------------------------------------------------------------------------

# P0 = immediate life threat, transfer now.  P1 = urgent, fast-track collection.
# P2 = moderate, normal flow.  P3 = low / non-emergency, normal flow.
FEW_SHOT_URGENCY = [
    # (convo_snippet, expected_urgency)
    # P0: someone is dying, active violence, fire with people trapped
    ("Caller: HELP! He's stabbing someone!", "P0"),
    ("Caller: My house is on fire and my kids are inside!", "P0"),
    ("Caller: He's not breathing, oh god please help!", "P0"),
    # P1: serious but not immediately life-threatening
    ("Caller: There's been a car accident, someone looks hurt.", "P1"),
    ("Caller: I think my neighbor is having a heart attack.", "P1"),
    # P2: moderate, property crime, non-injury situations
    ("Caller: Someone is breaking into my neighbor's car.", "P2"),
    ("Caller: There's a suspicious person walking around.", "P2"),
    # P3: low priority, non-emergency
    ("Caller: My cat is stuck in a tree.", "P3"),
    ("Caller: I want to report a noise complaint.", "P3"),
]


def assess_urgency(convo: str) -> str:
    """
    Assess the urgency of the call based on the FULL conversation so far.
    Called every turn so urgency can change as new info is revealed.
    Returns exactly one of: "P0", "P1", "P2", "P3".

    P0 = Immediate life threat (active violence, not breathing, fire with people).
         -> Transfer to human operator immediately, skip remaining questions.
    P1 = Urgent (injuries, heart attack, serious accident).
         -> Fast-track: collect emergency + location only, then transfer.
    P2 = Moderate (property crime, suspicious activity).
         -> Normal flow: collect all four fields, generate dispatcher lines, hang up.
    P3 = Low / non-emergency (noise complaint, cat in tree).
         -> Normal flow, advise caller this may not be a 911 matter.
    """
    # Prompt design: few-shot teaches the four levels; we pass the FULL convo
    # so the model sees everything (e.g. caller starts calm then escalates).
    few_shot_block = "\n".join(
        f"Conversation: {c}\nUrgency: {u}" for c, u in FEW_SHOT_URGENCY
    )
    prompt = f"""You are a 911 dispatch urgency analyst. Based on the full conversation, assign exactly one urgency level. Consider the caller's tone, words, and the nature of the situation.

Levels:
- P0: Immediate life threat (someone dying, active violence, fire with people trapped, not breathing)
- P1: Urgent (serious injury, heart attack, major accident with injuries)
- P2: Moderate (property crime, suspicious activity, non-injury situations)
- P3: Low / non-emergency (noise complaint, animal rescue, information request)

Examples:
{few_shot_block}

Current conversation:
{convo}

Respond with ONLY the urgency level (P0, P1, P2, or P3):"""
    client = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    text = (response.text or "").strip().upper()
    # Parse: accept "P0", "P1", "P2", "P3" only; default to P2 if model returns garbage.
    if text in ("P0", "P1", "P2", "P3"):
        return text
    # Try to find a valid level in the response (model might say "P0 - immediate...")
    for level in ("P0", "P1", "P2", "P3"):
        if level in text:
            return level
    return "P2"  # Safe default: moderate, normal flow.


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
    client = _get_client()
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    text = (response.text or "").strip()
    if not text:
        return "Thank you for providing all of this information. A 911 dispatcher will get in contact with you as soon as possible."
    return text
