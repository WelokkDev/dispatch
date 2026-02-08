"""
Gradium TTS service: converts dispatcher text into WAV audio files
that Twilio can play back to the caller via <Play>.
"""

import os
import asyncio
import uuid
import gradium

from config import GRADIUM_API_KEY

# Directory where generated audio files are stored temporarily.
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_cache")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Lazy-init Gradium client (created on first use so .env is loaded first).
_client = None

# Voice ID for "Emma" — pleasant, smooth US English female voice.
VOICE_ID = "YTpq7expH9539ERJ"

# Gradium server region — "us" or "eu". Change if your key is on a different region.
GRADIUM_REGION = os.getenv("GRADIUM_REGION", "us")
GRADIUM_BASE_URL = f"https://{GRADIUM_REGION}.api.gradium.ai/api/"


def _get_client():
    """Return the shared GradiumClient, creating it on first call."""
    global _client
    if _client is None:
        key = GRADIUM_API_KEY or os.getenv("GRADIUM_API_KEY")
        if not key:
            raise RuntimeError("GRADIUM_API_KEY is not set in .env")
        print(f"[Gradium] Initializing client with key: {key[:8]}...{key[-4:]}")
        print(f"[Gradium] Using region: {GRADIUM_REGION} ({GRADIUM_BASE_URL})")
        _client = gradium.client.GradiumClient(
            api_key=key,
            base_url=GRADIUM_BASE_URL,
        )
    return _client


def generate_audio(text: str, label: str = "") -> str:
    """
    Convert *text* to a WAV file using Gradium TTS.

    Args:
        text:  The dispatcher line to synthesise.
        label: Optional human-readable prefix for the filename.

    Returns:
        The filename (not full path) of the generated WAV, e.g.
        "greeting_a1b2c3d4.wav".  The file lives in AUDIO_DIR.
    """
    tag = label.replace(" ", "_")[:20] if label else "resp"
    filename = f"{tag}_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)

    async def _synthesise():
        client = _get_client()
        result = await client.tts(
            setup={
                "model_name": "default",
                "voice_id": VOICE_ID,
                "output_format": "wav",
            },
            text=text + " <flush>",
        )
        with open(filepath, "wb") as f:
            f.write(result.raw_data)

    asyncio.run(_synthesise())
    print(f"[Gradium TTS] Generated {filename} for: {text[:60]}...")
    return filename


def cleanup_audio(filename: str):
    """Delete an audio file after Twilio has fetched it."""
    path = os.path.join(AUDIO_DIR, filename)
    try:
        os.remove(path)
    except OSError:
        pass
