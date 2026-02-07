"""
Triage service: state machine for the dispatch call flow.
Order of checks matches TriageAI: emergency → location → name → number → free-form dispatcher lines.
No Gemini calls here; only calls into services.ai and state updates.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from services.ai import (
    extract_emergency,
    extract_location,
    extract_name,
    extract_phone,
    generate_next_dispatcher_line,
)


# One CallState per active call; Twilio session or call_id maps to this.
@dataclass
class CallState:
    """Holds all state for a single 911 call until hang up."""

    emergency: Optional[str] = None  # Extracted emergency type (under 5 words)
    location: Optional[str] = None   # Address or place, or "undefined"
    name: Optional[str] = None       # Caller name, or "undefined"
    number: Optional[str] = None    # Phone number, or "undefined"
    count: int = 1                  # Turn count for dispatcher lines (1, 2, 3...)
    redo: List[int] = field(default_factory=lambda: [0, 0, 0])  # Retries: location, name, phone
    convo: str = ""                 # Full transcript: "Dispatcher: ... Caller: ..."


def generate_ai_response(state: CallState, voice_input: str) -> tuple[CallState, str, bool]:
    """
    One step of the dispatch flow: append caller line to convo, then either
    extract a field (emergency, location, name, number) or generate the next
    dispatcher line. Returns (updated_state, spoken_line, hang_up).
    """
    # Step 1: Append this caller utterance to the transcript.
    state = dataclass_replace(state, convo=state.convo + f"\nCaller: {voice_input}\nDispatcher: ")

    # Step 2: If we don't have emergency yet, extract it and return fixed follow-up.
    if state.emergency is None or state.emergency == "":
        emergency = extract_emergency(state.convo)
        state = dataclass_replace(state, emergency=emergency)
        spoken = "Okay, stay calm. Can you tell me your location?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False

    # Step 3: If we don't have location, extract it; allow one re-ask if "undefined".
    if state.location is None or state.location == "":
        location = extract_location(state.convo)
        if location == "undefined" and state.redo[0] < 1:
            spoken = "Okay, stay calm. Tell me your location or where you remember being last?"
            state = dataclass_replace(state, redo=[state.redo[0] + 1, state.redo[1], state.redo[2]], convo=state.convo + spoken)
            return state, spoken, False
        state = dataclass_replace(state, location=location)
        spoken = "Okay, can I get your full name?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False

    # Step 4: If we don't have name, extract it; allow one re-ask.
    if state.name is None or state.name == "":
        name = extract_name(state.convo)
        if name == "undefined" and state.redo[1] < 1:
            spoken = "I need you to remain calm; we will get help to you as soon as possible. Can you give me your name again?"
            state = dataclass_replace(state, redo=[state.redo[0], state.redo[1] + 1, state.redo[2]], convo=state.convo + spoken)
            return state, spoken, False
        state = dataclass_replace(state, name=name)
        spoken = "And what's your phone number just in case we're disconnected?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False

    # Step 5: If we don't have number, extract it; allow one re-ask.
    if state.number is None or state.number == "":
        number = extract_phone(state.convo)
        if number == "undefined" and state.redo[2] < 1:
            spoken = "Don't worry, we will get help to you as soon as possible. I need a phone number?"
            state = dataclass_replace(state, redo=[state.redo[0], state.redo[1], state.redo[2] + 1], convo=state.convo + spoken)
            return state, spoken, False
        state = dataclass_replace(state, number=number)

    # Step 6: All collected. Generate next dispatcher line; count 1 = more details, count 2 = ask more, count >= 3 = end call.
    should_end = state.count >= 3
    line = generate_next_dispatcher_line(state.convo, state.count, should_end_call=should_end)
    state = dataclass_replace(state, convo=state.convo + line, count=state.count + 1)
    return state, line, should_end


def dataclass_replace(s: CallState, **kwargs) -> CallState:
    """Return a new CallState with the given fields updated (immutable update)."""
    d = {f: getattr(s, f) for f in ("emergency", "location", "name", "number", "count", "redo", "convo")}
    d.update(kwargs)
    return CallState(**d)
