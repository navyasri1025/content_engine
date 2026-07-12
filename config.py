"""
Configuration module — loads API keys and model settings.

Uses python-dotenv to load from .env file in the same directory.

Providers:
  - OpenRouter   : text generation (tagline, blog, social posts, video brief, audio)
  - Pollinations : image generation — FLUX.1-dev (no API key required)
  - Local        : video generation — Ken Burns effect via imageio + Pillow + NumPy
  - Edge TTS     : audio narration — Microsoft Edge TTS (no API key required)
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env in the same directory as this file
load_dotenv(Path(__file__).parent / ".env")

# ── Logging setup (configure once here so all modules inherit it) ──────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("config")

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ── Model IDs ─────────────────────────────────────────────────────────────────
# OpenRouter model for text generation (tagline, blog, social)
TEXT_MODEL = "openai/gpt-4.1-mini"

# Pollinations AI — FLUX.1-dev (no key needed)
IMAGE_PROVIDER = "pollinations"

# OpenRouter model for video brief / audio script (text-only)
VIDEO_BRIEF_MODEL = "openai/gpt-4.1-mini"

# Edge TTS voice for narration (no API key required)
# Full list: `edge-tts --list-voices`
TTS_VOICE = "en-US-AriaNeural"

# ── Availability flags ────────────────────────────────────────────────────────
HAS_OPENROUTER = bool(OPENROUTER_API_KEY)
HAS_VIDEO      = HAS_OPENROUTER

# ── Log key status at startup ─────────────────────────────────────────────────
logger.info("API key status:")
logger.info("  OpenRouter (text)    : %s", "✓ configured" if HAS_OPENROUTER else "✗ missing — set OPENROUTER_API_KEY")
logger.info("  OpenRouter (briefs)  : %s", "✓ configured" if HAS_VIDEO      else "✗ missing — set OPENROUTER_API_KEY")
logger.info("  Pollinations (image) : ✓ no key required")
logger.info("  Video (Ken Burns)    : ✓ fully local — no key required")
logger.info("  Edge TTS (audio)     : ✓ no key required")
