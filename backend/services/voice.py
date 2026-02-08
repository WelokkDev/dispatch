"""
Gradium TTS service: converts dispatcher text into WAV audio files
that Twilio can play back to the caller via <Play>.

Performance strategy:
  - All FIXED dispatcher lines (from triage.py) are pre-generated at startup
    and cached in memory.  These account for ~90% of all responses.
  - Only dynamically generated lines (from generate_next_dispatcher_line) hit
    the Gradium API at call time.
  - Pre-caching runs in parallel (4 concurrent) so startup takes ~15-20s
    instead of 60+.
"""

import os
import time
import uuid
import asyncio
import gradium

from config import GRADIUM_API_KEY

# Directory where generated audio files are stored temporarily.
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_cache")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Gradium config
GRADIUM_REGION = os.getenv("GRADIUM_REGION", "us")
GRADIUM_VOICE_ID = os.getenv("GRADIUM_VOICE_ID", "YTpq7expH9539ERJ")
GRADIUM_BASE_URL = f"https://{GRADIUM_REGION}.api.gradium.ai/api/"

# ═══════════════════════════════════════════════════════════════════════════════
# Audio cache: text → filename  (pre-generated at startup for fixed lines)
# ═══════════════════════════════════════════════════════════════════════════════
_audio_cache: dict[str, str] = {}

# Every fixed dispatcher line from triage.py and app.py.
# These never change, so we generate them ONCE at startup.
FIXED_LINES = [
    # Greeting (app.py)
    "911, what is your emergency?",
    # P0 (triage.py _handle_p0)
    "Stay on the line. I'm connecting you to an emergency operator right now.",
    # P1 (triage.py _handle_p1)
    "I can hear you're upset. Can you tell me what's happening? What is the emergency?",
    "Okay, stay calm. Can you tell me your location?",
    "I need you to stay calm. Can you tell me where you are or the nearest landmark?",
    "Help is on the way. I'm transferring you to a dispatcher who can assist you further.",
    # P2/P3 (triage.py _handle_normal)
    "I'm here to help. Can you tell me what's happening? What is the emergency?",
    # "Okay, stay calm. Can you tell me your location?" ← same as P1, already cached
    "Okay, stay calm. Tell me your location or where you remember being last?",
    "Okay, can I get your full name?",
    "I need you to remain calm; we will get help to you as soon as possible. Can you give me your name again?",
    "And what's your phone number just in case we're disconnected?",
    "Don't worry, we will get help to you as soon as possible. I need a phone number?",
    # App-level (app.py voice_respond)
    "Transferring you now. Please stay on the line.",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Core TTS generation
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_wav_bytes(text: str) -> bytes:
    """Generate WAV audio bytes from text using Gradium SDK (sync wrapper)."""
    key = GRADIUM_API_KEY or os.getenv("GRADIUM_API_KEY")
    if not key:
        raise RuntimeError("GRADIUM_API_KEY is not set in .env")

    async def _run():
        client = gradium.client.GradiumClient(
            api_key=key,
            base_url=GRADIUM_BASE_URL,
        )
        result = await client.tts(
            setup={
                "model_name": "default",
                "voice_id": GRADIUM_VOICE_ID,
                "output_format": "wav",
            },
            text=text + " <flush>",
        )
        return result.raw_data

    return asyncio.run(_run())


def generate_audio(text: str, label: str = "") -> str:
    """
    Convert *text* to a WAV file using Gradium TTS.
    Returns the cached filename instantly if available (zero latency).
    """
    # Check pre-cache first — instant return, zero TTS latency.
    if text in _audio_cache:
        print(f"[Gradium TTS] Cache HIT: {text[:60]}...")
        return _audio_cache[text]

    # Cache miss — generate live (only happens for dynamic dispatcher lines).
    tag = label.replace(" ", "_")[:20] if label else "resp"
    filename = f"{tag}_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)

    t0 = time.time()
    audio_bytes = _generate_wav_bytes(text)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    elapsed = time.time() - t0

    print(f"[Gradium TTS] Generated {filename} in {elapsed:.1f}s for: {text[:60]}...")
    return filename


# ═══════════════════════════════════════════════════════════════════════════════
# Startup pre-caching (parallel)
# ═══════════════════════════════════════════════════════════════════════════════

def precache_fixed_lines():
    """
    Generate audio for ALL fixed dispatcher lines at startup.
    Runs up to 4 TTS calls in parallel to speed up startup.
    """
    key = GRADIUM_API_KEY or os.getenv("GRADIUM_API_KEY")
    if not key:
        print("[Startup] WARNING: GRADIUM_API_KEY not set, skipping pre-cache.")
        return

    print(f"[Startup] Pre-caching {len(FIXED_LINES)} fixed dispatcher lines...")
    t_start = time.time()

    async def _gen_one(line: str) -> bytes:
        client = gradium.client.GradiumClient(
            api_key=key,
            base_url=GRADIUM_BASE_URL,
        )
        result = await client.tts(
            setup={
                "model_name": "default",
                "voice_id": GRADIUM_VOICE_ID,
                "output_format": "wav",
            },
            text=line + " <flush>",
        )
        return result.raw_data

    async def _precache_all():
        sem = asyncio.Semaphore(4)  # max 4 concurrent WebSocket connections

        async def _limited(line: str) -> bytes:
            async with sem:
                return await _gen_one(line)

        return await asyncio.gather(*[_limited(line) for line in FIXED_LINES])

    results = asyncio.run(_precache_all())

    for i, (line, audio_bytes) in enumerate(zip(FIXED_LINES, results)):
        filename = f"cached_{i:02d}.wav"
        filepath = os.path.join(AUDIO_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        _audio_cache[line] = filename
        print(f"  [{i+1}/{len(FIXED_LINES)}] {line[:55]}...")

    elapsed = time.time() - t_start
    print(f"[Startup] Pre-cached {len(_audio_cache)} lines in {elapsed:.1f}s. Ready for calls!")


def cleanup_audio(filename: str):
    """Delete an audio file after Twilio has fetched it."""
    # Never delete pre-cached files.
    if filename in _audio_cache.values():
        return
    path = os.path.join(AUDIO_DIR, filename)
    try:
        os.remove(path)
    except OSError:
        pass
