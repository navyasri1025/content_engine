"""
Image generation module — Hero image via Pollinations AI (FLUX.1-dev).

Uses the Pollinations AI image endpoint which proxies FLUX.1-dev.
No API key required — the endpoint is publicly accessible.

API:  https://image.pollinations.ai/prompt/{encoded_prompt}?{params}
Docs: https://pollinations.ai
"""

import logging
import time
import urllib.parse
from pathlib import Path

import requests

# ── Logger ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("image_gen")

# ── Output directory ──────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"

# ── Style map ─────────────────────────────────────────────────────────────────
# Maps brand tones to visual style descriptors for FLUX.1-dev
STYLE_MAP = {
    "playful": "bright flat illustration, vibrant colors, whimsical shapes, cartoon-like",
    "premium": "photorealistic, studio lighting, rich textures, deep shadows, luxurious, cinematic",
    "eco": "watercolour style, natural tones, earth colors, organic textures, soft lighting",
    "professional": "clean modern, minimalist, polished, corporate aesthetic, sharp lighting",
}
DEFAULT_STYLE = "clean modern, minimalist, polished"

# Pollinations AI endpoint
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


def build_image_prompt(product: str, tagline: str, tone: str) -> str:
    """
    Build a detailed FLUX.1-dev prompt.

    Formula: subject + style (from tone) + composition + constraints
    """
    style = STYLE_MAP.get(tone.lower().strip(), DEFAULT_STYLE)
    prompt = (
        f"A professional marketing hero image featuring {product}. "
        f"Style: {style}. "
        f"Centered composition, shallow depth of field, 16:9 aspect ratio. "
        f"The mood conveys: '{tagline}'. "
        f"No text, no logos, no watermarks. "
        f"Clean background, professional lighting, high detail, 8k quality."
    )
    logger.debug("Built image prompt: %s", prompt)
    return prompt


def generate_image(product: str, tagline: str, tone: str) -> str | None:
    """
    Generate a campaign hero image using Pollinations AI (FLUX.1-dev).

    Downloads the image to a local file and returns the local path on success,
    or None on failure (error is logged to terminal).

    Returns:
        str | None: Local file path of the downloaded image, or None on failure.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    prompt = build_image_prompt(product, tagline, tone)
    encoded_prompt = urllib.parse.quote(prompt)

    # Build the Pollinations URL with parameters
    params = {
        "width": 1280,
        "height": 720,
        "model": "flux",        # FLUX.1-dev via Pollinations
        "seed": int(time.time()) % 100000,
        "nologo": "true",
        "enhance": "false",
    }
    query_string = urllib.parse.urlencode(params)
    image_url = f"{POLLINATIONS_URL.format(prompt=encoded_prompt)}?{query_string}"

    logger.info("→ [Pollinations AI] GET image request")
    logger.info("  Model  : FLUX.1-dev (via pollinations.ai)")
    logger.info("  Size   : 1280×720")
    logger.info("  URL    : %s", image_url[:120] + "..." if len(image_url) > 120 else image_url)

    try:
        resp = requests.get(image_url, timeout=90, stream=False)
        logger.info("  GET status   : %d", resp.status_code)
        logger.info("  Content-Type : %s", resp.headers.get("content-type", "unknown"))

        if resp.status_code != 200:
            logger.error(
                "← [Pollinations AI] HTTP %d | Body: %s",
                resp.status_code,
                resp.text[:300],
            )
            return None

        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type:
            logger.error(
                "← [Pollinations AI] Unexpected content-type: %s | Body: %s",
                content_type,
                resp.text[:300],
            )
            return None

        # Save image to a local file
        ts = int(time.time())
        local_path = OUTPUT_DIR / f"hero_image_{ts}.jpg"
        local_path.write_bytes(resp.content)
        logger.info("← [Pollinations AI] Image saved locally: %s (%d KB)", local_path, len(resp.content) // 1024)
        return str(local_path)

    except requests.exceptions.Timeout:
        logger.error("← [Pollinations AI] Request timed out after 90s")
        return None
    except requests.exceptions.ConnectionError as exc:
        logger.error("← [Pollinations AI] Connection error: %s", exc)
        return None
    except Exception as exc:
        logger.error("← [Pollinations AI] Unexpected error: %s", exc, exc_info=True)
        return None
