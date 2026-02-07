"""
Triage service: state machine for the dispatch call flow.
Urgency (P0–P3) is assessed EVERY turn before deciding what to do next.
P0/P1 can short-circuit the normal collection flow and trigger an operator transfer.
No Gemini calls here; only calls into services.ai and state updates.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from services.ai import (
    assess_urgency,
    extract_emergency,
    extract_location,
    extract_name,
    extract_phone,
    generate_next_dispatcher_line,
)


# One CallState per active call; Twilio session or call_id maps to this.
@dataclass
class CallState:
    """Holds all state for a single 911 call until hang up or transfer."""

    emergency: Optional[str] = None  # Extracted emergency type (under 5 words)
    location: Optional[str] = None   # Address or place, or "undefined"
    name: Optional[str] = None       # Caller name, or "undefined"
    number: Optional[str] = None     # Phone number, or "undefined"
    urgency: Optional[str] = None    # Current urgency: P0, P1, P2, P3 (updated every turn)
    transfer: bool = False           # True = call should be transferred to human operator
    count: int = 1                   # Turn count for dispatcher lines (1, 2, 3...)
    redo: List[int] = field(default_factory=lambda: [0, 0, 0])  # Retries: location, name, phone
    convo: str = ""                  # Full transcript: "Dispatcher: ... Caller: ..."


def generate_ai_response(state: CallState, voice_input: str) -> tuple:
    """
    One step of the dispatch flow. Returns (updated_state, spoken_line, hang_up, transfer).

    Every turn:
      1. Append caller speech to convo.
      2. Assess urgency (P0–P3) — runs EVERY turn, can change as caller reveals more.
      3. Branch on urgency:
         - P0: Immediate transfer. Skip all remaining questions.
         - P1: Fast-track — collect emergency + location only, then transfer.
         - P2/P3: Normal flow — collect all four fields, then generate dispatcher lines.
    """
    # -------------------------------------------------------------------------
    # Step 1: Append this caller utterance to the transcript.
    # -------------------------------------------------------------------------
    state = dataclass_replace(state, convo=state.convo + f"\nCaller: {voice_input}\nDispatcher: ")

    # -------------------------------------------------------------------------
    # Step 2: Assess urgency EVERY turn. This is the key difference from before.
    # The model sees the FULL convo, so if someone starts calm ("there's been an
    # accident") then escalates ("oh god he's not breathing"), urgency goes up.
    # -------------------------------------------------------------------------
    urgency = assess_urgency(state.convo)
    state = dataclass_replace(state, urgency=urgency)

    # -------------------------------------------------------------------------
    # Step 3: Branch on urgency level.
    # -------------------------------------------------------------------------

    if urgency == "P0":
        # P0: IMMEDIATE life threat. Don't waste time asking for name/phone.
        # Try to extract emergency and location from what we already have (one
        # quick pass), then transfer immediately.
        return _handle_p0(state)

    if urgency == "P1":
        # P1: Urgent. Collect emergency + location only (skip name/phone), then transfer.
        return _handle_p1(state)

    # P2 or P3: Normal flow — collect all four fields, then dispatcher lines.
    return _handle_normal(state)


# =============================================================================
# P0 handler: immediate transfer, minimal collection
# =============================================================================

def _handle_p0(state: CallState) -> tuple:
    """
    P0 = immediate life threat. We try one quick extraction pass for emergency
    and location (from what the caller already said), then transfer right away.
    We do NOT ask follow-up questions — every second counts.
    """
    # Try to extract emergency if we don't have it yet (from existing convo only).
    if not state.emergency:
        emergency = extract_emergency(state.convo)
        state = dataclass_replace(state, emergency=emergency)

    # Try to extract location if we don't have it yet.
    if not state.location:
        location = extract_location(state.convo)
        if location != "undefined":
            state = dataclass_replace(state, location=location)
        # If location is "undefined", that's okay for P0 — we still transfer.

    # Immediately transfer to operator.
    spoken = "Stay on the line. I'm connecting you to an emergency operator right now."
    state = dataclass_replace(state, transfer=True, convo=state.convo + spoken)
    return state, spoken, False, True  # hang_up=False, transfer=True


# =============================================================================
# P1 handler: fast-track — collect emergency + location, then transfer
# =============================================================================

def _handle_p1(state: CallState) -> tuple:
    """
    P1 = urgent. We need emergency type and location before transferring so the
    operator has context. Skip name and phone — not worth the time.
    """
    # Extract emergency if missing.
    if not state.emergency:
        emergency = extract_emergency(state.convo)
        state = dataclass_replace(state, emergency=emergency)
        spoken = "Okay, stay calm. Can you tell me your location?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False, False  # Continue, need location next.

    # Extract location if missing; allow one re-ask.
    if not state.location:
        location = extract_location(state.convo)
        if location == "undefined" and state.redo[0] < 1:
            spoken = "I need you to stay calm. Can you tell me where you are or the nearest landmark?"
            state = dataclass_replace(
                state,
                redo=[state.redo[0] + 1, state.redo[1], state.redo[2]],
                convo=state.convo + spoken,
            )
            return state, spoken, False, False
        state = dataclass_replace(state, location=location if location != "undefined" else None)

    # We have emergency (and possibly location). Transfer now.
    spoken = "Help is on the way. I'm transferring you to a dispatcher who can assist you further."
    state = dataclass_replace(state, transfer=True, convo=state.convo + spoken)
    return state, spoken, False, True  # hang_up=False, transfer=True


# =============================================================================
# P2/P3 handler: normal flow — collect all four fields, then dispatcher lines
# =============================================================================

def _handle_normal(state: CallState) -> tuple:
    """
    P2/P3 = moderate or low. Full collection: emergency → location → name →
    number → generate dispatcher lines → eventually hang up.
    This is the original TriageAI-style flow.
    """
    # --- Extract emergency if missing ---
    if not state.emergency:
        emergency = extract_emergency(state.convo)
        state = dataclass_replace(state, emergency=emergency)
        spoken = "Okay, stay calm. Can you tell me your location?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False, False

    # --- Extract location if missing; allow one re-ask ---
    if not state.location:
        location = extract_location(state.convo)
        if location == "undefined" and state.redo[0] < 1:
            spoken = "Okay, stay calm. Tell me your location or where you remember being last?"
            state = dataclass_replace(
                state,
                redo=[state.redo[0] + 1, state.redo[1], state.redo[2]],
                convo=state.convo + spoken,
            )
            return state, spoken, False, False
        state = dataclass_replace(state, location=location)
        spoken = "Okay, can I get your full name?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False, False

    # --- Extract name if missing; allow one re-ask ---
    if not state.name:
        name = extract_name(state.convo)
        if name == "undefined" and state.redo[1] < 1:
            spoken = "I need you to remain calm; we will get help to you as soon as possible. Can you give me your name again?"
            state = dataclass_replace(
                state,
                redo=[state.redo[0], state.redo[1] + 1, state.redo[2]],
                convo=state.convo + spoken,
            )
            return state, spoken, False, False
        state = dataclass_replace(state, name=name)
        spoken = "And what's your phone number just in case we're disconnected?"
        state = dataclass_replace(state, convo=state.convo + spoken)
        return state, spoken, False, False

    # --- Extract phone if missing; allow one re-ask ---
    if not state.number:
        number = extract_phone(state.convo)
        if number == "undefined" and state.redo[2] < 1:
            spoken = "Don't worry, we will get help to you as soon as possible. I need a phone number?"
            state = dataclass_replace(
                state,
                redo=[state.redo[0], state.redo[1], state.redo[2] + 1],
                convo=state.convo + spoken,
            )
            return state, spoken, False, False
        state = dataclass_replace(state, number=number)
        # Fall through to generate dispatcher line.

    # --- All fields collected. Generate next dispatcher line. ---
    # count 1 = more details, count 2 = ask more, count >= 3 = end call.
    should_end = state.count >= 3
    line = generate_next_dispatcher_line(state.convo, state.count, should_end_call=should_end)
    state = dataclass_replace(state, convo=state.convo + line, count=state.count + 1)
    return state, line, should_end, False  # hang_up if should_end, no transfer


# =============================================================================
# Helper
# =============================================================================

def dataclass_replace(s: CallState, **kwargs) -> CallState:
    """Return a new CallState with the given fields updated (immutable update)."""
    fields = ("emergency", "location", "name", "number", "urgency", "transfer", "count", "redo", "convo")
    d = {f: getattr(s, f) for f in fields}
    d.update(kwargs)
    return CallState(**d)
