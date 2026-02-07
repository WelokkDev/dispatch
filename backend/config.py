"""
Centralized config for the dispatch backend.
Loads API keys and model name from environment; no secrets in code.
"""
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
