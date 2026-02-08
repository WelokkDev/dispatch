"""
Centralized config for the dispatch backend.
Loads API keys and model name from environment; no secrets in code.
"""
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Gradium TTS
GRADIUM_API_KEY = os.getenv("GRADIUM_API_KEY")
