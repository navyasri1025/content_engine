"""
Video generation module — fully local, zero API keys required.

Pipeline
--------
1. Ken Burns video  — zooms + pans the hero image using Pillow, NumPy, and
                      imageio (ffmpeg backend).  No external video API needed.
2. Edge TTS audio   — generates an MP3 narration from the voiceover script
                      using Microsoft Edge TTS (edge-tts).  No API key needed.
3. Mux              — combines the silent MP4 + MP3 into a final MP4 using
                      a bundled ffmpeg subprocess call.

Dependencies (all pip-installable, no keys required):
    pip install imageio[ffmpeg] Pillow numpy edge-tts
"""

from __future__ import annotations

import asyncio
import logging
import math
import subprocess
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from config import TTS_VOICE

logger = logging.getLogger("video_gen")

# ── Output directory ──────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"

# ── Video settings ────────────────────────────────────────────────────────────
VIDEO_W, VIDEO_H = 1280, 720   # output resolution
FPS              = 24           # frames per second
VIDEO_DURATION   = 10.0         # seconds of Ken Burns animation


# ─────────────────────────────────────────────────────────────────────────────
#  Helper — cosine ease-in-out interpolation
# ─────────────────────────────────────────────────────────────────────────────
def _ease(t: float) -> float:
    """Smooth cosine ease-in-out over t ∈ [0, 1]."""
    return (1 - math.cos(math.pi * t)) / 2


# ─────────────────────────────────────────────────────────────────────────────
#  Step 1 — Ken Burns video (silent MP4)
# ─────────────────────────────────────────────────────────────────────────────
def _build_ken_burns_video(image_url: str, output_path: Path) -> tuple[bool, str | None]:
    """
    Load an image from a local file path or a URL, apply a Ken Burns zoom-and-pan
    effect, and write a silent MP4 to `output_path`.

    Returns (success: bool, error_message: str | None).
    """
    import imageio  # local import so missing package gives a clear error

    # ── 1a. Load the image (local path or URL) ────────────────────────────────
    local_path = Path(image_url)
    if local_path.exists():
        logger.info("  [ken-burns] Loading source image from local file: %s", image_url)
        try:
            img = Image.open(local_path).convert("RGB")
        except Exception as exc:
            return False, f"Cannot open local image: {exc}"
    else:
        logger.info("  [ken-burns] Downloading source image: %s", image_url[:80])
        try:
            resp = requests.get(image_url, timeout=60)
            resp.raise_for_status()
        except Exception as exc:
            return False, f"Image download failed: {exc}"
        try:
            import io
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception as exc:
            return False, f"Cannot open downloaded image: {exc}"

    iw, ih = img.size
    logger.info("  [ken-burns] Source image size: %d×%d", iw, ih)

    # ── 1b. Compute Ken Burns parameters ─────────────────────────────────────
    # Start crop: slight zoom-in at centre (80 % of image)
    # End crop  : panned slightly right and further zoomed (72 % of image)
    # Values are fractions of the image dimensions.
    zoom_start = 0.80   # crop = 80 % of original at frame 0
    zoom_end   = 0.72   # crop = 72 % of original at last frame
    # Pan: shift the crop centre horizontally by ±pan_x and vertically by ±pan_y
    pan_x_start, pan_y_start = 0.0,  0.0    # centre of image (normalised offset)
    pan_x_end,   pan_y_end   = 0.05, -0.03  # slight right-and-up pan

    total_frames = int(VIDEO_DURATION * FPS)
    logger.info("  [ken-burns] Rendering %d frames at %d fps (%0.1fs)", total_frames, FPS, VIDEO_DURATION)

    # ── 1c. Write frames via imageio ─────────────────────────────────────────
    writer = imageio.get_writer(
        str(output_path),
        fps=FPS,
        codec="libx264",
        quality=None,          # use ffmpeg_params instead
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",    # broadest player compatibility
            "-crf", "22",             # good quality / size balance
            "-preset", "fast",
        ],
        macro_block_size=None,
    )

    try:
        img_np = np.array(img)

        for frame_idx in range(total_frames):
            t = frame_idx / max(total_frames - 1, 1)
            e = _ease(t)

            # Interpolate zoom and pan
            zoom  = zoom_start  + (zoom_end  - zoom_start)  * e
            pan_x = pan_x_start + (pan_x_end - pan_x_start) * e
            pan_y = pan_y_start + (pan_y_end - pan_y_start) * e

            # Crop dimensions in source-image pixels
            cw = int(iw * zoom)
            ch = int(ih * zoom)

            # Crop centre (clamped so crop stays inside image)
            cx = int(iw * (0.5 + pan_x))
            cy = int(ih * (0.5 + pan_y))

            x0 = max(0, min(cx - cw // 2, iw - cw))
            y0 = max(0, min(cy - ch // 2, ih - ch))
            x1 = x0 + cw
            y1 = y0 + ch

            # Crop and resize to output resolution
            crop = img_np[y0:y1, x0:x1]
            frame_img = Image.fromarray(crop).resize(
                (VIDEO_W, VIDEO_H), Image.LANCZOS
            )
            writer.append_data(np.array(frame_img))

            if frame_idx % FPS == 0:
                logger.info(
                    "  [ken-burns] Frame %d/%d  zoom=%.2f  pan=(%.3f,%.3f)",
                    frame_idx, total_frames, zoom, pan_x, pan_y,
                )
    finally:
        writer.close()

    logger.info("  [ken-burns] Silent MP4 written: %s", output_path)
    return True, None


# ─────────────────────────────────────────────────────────────────────────────
#  Step 2 — Edge TTS narration (MP3)
# ─────────────────────────────────────────────────────────────────────────────
def _build_tts_audio(script: str, output_path: Path) -> tuple[bool, str | None]:
    """
    Synthesise `script` to an MP3 at `output_path` using Edge TTS.

    Returns (success: bool, error_message: str | None).
    """
    try:
        import edge_tts  # local import
    except ImportError:
        return False, "edge-tts not installed. Run: pip install edge-tts"

    logger.info("  [edge-tts] Synthesising narration | voice=%s | chars=%d", TTS_VOICE, len(script))

    async def _synth() -> None:
        communicate = edge_tts.Communicate(script, TTS_VOICE)
        await communicate.save(str(output_path))

    try:
        asyncio.run(_synth())
    except RuntimeError:
        # Already inside a running event loop (e.g. Jupyter / some Streamlit modes)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(asyncio.run, _synth()).result()

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("  [edge-tts] Audio saved: %s (%d KB)", output_path, output_path.stat().st_size // 1024)
        return True, None
    return False, "edge-tts produced no output file."


# ─────────────────────────────────────────────────────────────────────────────
#  Step 3 — Mux video + audio with ffmpeg
# ─────────────────────────────────────────────────────────────────────────────
def _mux(video_path: Path, audio_path: Path, output_path: Path) -> tuple[bool, str | None]:
    """
    Combine silent MP4 + MP3 into a final MP4 using ffmpeg.
    Audio is looped/trimmed to match the video duration.
    """
    import shutil
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        # imageio bundles ffmpeg — try to locate it
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

    if not ffmpeg_bin:
        return False, "ffmpeg not found on PATH. Install it or let imageio[ffmpeg] provide it."

    cmd = [
        ffmpeg_bin,
        "-y",                           # overwrite without prompt
        "-i",  str(video_path),         # silent video
        "-i",  str(audio_path),         # narration audio
        "-c:v", "copy",                 # copy video stream (no re-encode)
        "-c:a", "aac",                  # encode audio to AAC
        "-b:a", "128k",
        "-shortest",                    # trim to shortest stream
        "-movflags", "+faststart",      # web-optimised MP4
        str(output_path),
    ]
    logger.info("  [mux] Running ffmpeg: %s", " ".join(cmd))

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            err = proc.stderr[-600:] if proc.stderr else "(no stderr)"
            logger.error("  [mux] ffmpeg exited %d:\n%s", proc.returncode, err)
            return False, f"ffmpeg mux failed (exit {proc.returncode}):\n{err}"
        logger.info("  [mux] Final video written: %s", output_path)
        return True, None
    except subprocess.TimeoutExpired:
        return False, "ffmpeg mux timed out (>120 s)."
    except Exception as exc:
        return False, f"ffmpeg mux error: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
#  Public API — generate_video
# ─────────────────────────────────────────────────────────────────────────────
def generate_video(
    product: str,
    tagline: str,
    tone: str,
    audience: str,
    image_url: str | None = None,
    voiceover_script: str | None = None,
) -> tuple[str | None, str | None]:
    """
    Build a promotional MP4 locally using Ken Burns + Edge TTS.

    Parameters
    ----------
    product, tagline, tone, audience : str
        Campaign metadata (used to build a default voiceover if none given).
    image_url : str | None
        Pollinations AI image URL to animate.  If None, returns an error.
    voiceover_script : str | None
        Text to synthesise.  Falls back to a simple built-in script.

    Returns
    -------
    (path: str | None, error: str | None)
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = int(time.time())

    # ── Guard: need an image ──────────────────────────────────────────────────
    if not image_url:
        msg = "No image URL supplied to video generator. Generate the hero image first."
        logger.error("[video_gen] %s", msg)
        return None, msg

    # ── Build a fallback script if none provided ──────────────────────────────
    if not voiceover_script:
        voiceover_script = (
            f"Introducing {product}. {tagline}. "
            f"Crafted for {audience}. Experience the difference today."
        )
        logger.info("[video_gen] Using built-in voiceover script")

    logger.info("[video_gen] === Starting local Ken Burns video pipeline ===")
    logger.info("[video_gen]   Product   : %s", product)
    logger.info("[video_gen]   Tone      : %s", tone)
    logger.info("[video_gen]   Script    : %s", voiceover_script[:80])

    silent_mp4  = OUTPUT_DIR / f"video_silent_{ts}.mp4"
    narration   = OUTPUT_DIR / f"narration_{ts}.mp3"
    final_mp4   = OUTPUT_DIR / f"campaign_video_{ts}.mp4"

    # ── Step 1: Ken Burns silent video ───────────────────────────────────────
    logger.info("[video_gen] Step 1/3 — Ken Burns silent video")
    ok, err = _build_ken_burns_video(image_url, silent_mp4)
    if not ok:
        return None, f"Ken Burns render failed: {err}"

    # ── Step 2: Edge TTS audio ────────────────────────────────────────────────
    logger.info("[video_gen] Step 2/3 — Edge TTS narration")
    ok, err = _build_tts_audio(voiceover_script, narration)
    if not ok:
        # Audio failure is non-fatal: return the silent video
        logger.warning("[video_gen] TTS failed (%s) — returning silent video", err)
        silent_mp4.rename(final_mp4)
        return str(final_mp4), f"Note: audio narration failed ({err}). Silent video returned."

    # ── Step 3: Mux ───────────────────────────────────────────────────────────
    logger.info("[video_gen] Step 3/3 — Mux video + audio")
    ok, err = _mux(silent_mp4, narration, final_mp4)

    # Clean up intermediate files
    for f in [silent_mp4, narration]:
        try:
            f.unlink(missing_ok=True)
        except OSError:
            pass

    if not ok:
        # Mux failure — return the silent video if it still exists
        if silent_mp4.exists():
            silent_mp4.rename(final_mp4)
            return str(final_mp4), f"Note: audio mux failed ({err}). Silent video returned."
        return None, f"Video mux failed: {err}"

    size_kb = final_mp4.stat().st_size // 1024
    logger.info("[video_gen] === Done — %s (%d KB) ===", final_mp4.name, size_kb)
    return str(final_mp4), None
