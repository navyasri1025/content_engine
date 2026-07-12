# AI Content Engine

One brief in → five creative assets out.

A **Streamlit** application that takes a product brief and automatically generates:

1. **Tagline** — few-shot prompting via OpenRouter GPT-4.1-mini
2. **Blog Intro** — role-based prompting via OpenRouter GPT-4.1-mini
3. **Social Posts** — structured JSON via OpenRouter GPT-4.1-mini
4. **Hero Image** — FLUX.1-dev via Pollinations AI (no API key required)
5. **Promo Video** — LTX-Video via fal.ai
6. **Video Creative Brief** — storyboard via OpenRouter GPT-4.1-mini
7. **Audio Voiceover Script** — via OpenRouter GPT-4.1-mini

---

## Tech Stack

| Asset             | Provider           | Model / Endpoint                          |
|-------------------|--------------------|-------------------------------------------|
| Text Generation   | OpenRouter         | `openai/gpt-4.1-mini`                     |
| Image Generation  | **Pollinations AI**| `FLUX.1-dev` (no key required)            |
| Video Generation  | **fal.ai**         | `fal-ai/ltx-video` (LTX-Video)            |
| Video Brief       | OpenRouter         | `openai/gpt-4.1-mini`                     |

---

## Setup

### 1. Install dependencies

```bash
cd content_engine
pip install -r requirements.txt
```

### 2. Configure API keys

Create or edit `.env` in the `content_engine/` directory:

```env
# OpenRouter — text generation (tagline, blog, social posts)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# OpenRouter — video brief & audio script (can reuse the same key)
OPENROUTER_VIDEO_KEY=sk-or-v1-xxxxxxxxxxxx

# fal.ai — LTX-Video text-to-video generation
# Sign up at https://fal.ai, create an API key in the dashboard
FAL_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

> **Pollinations AI (image)** requires no API key — it is publicly accessible.

### 3. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Pipeline

```
Brief → Tagline ──→ Blog Intro
           │
           └──→ FLUX.1-dev Image → LTX-Video + Brief + Audio
```

---

## Project Structure

```
content_engine/
├── .env                  # API keys (not committed)
├── app.py                # Streamlit UI + pipeline orchestration
├── config.py             # API keys, model IDs, logging setup
├── text_gen.py           # Tagline, blog, social posts (OpenRouter)
├── image_gen.py          # FLUX.1-dev via Pollinations AI (no key)
├── video_gen.py          # LTX-Video via fal.ai + brief/audio via OpenRouter
├── requirements.txt
└── README.md
```

---

## API Key Status (sidebar)

Status indicators in the sidebar:
- **OpenRouter (Text):** ✅ Connected / ❌ No key
- **Pollinations (Image):** ✅ No key needed (always available)
- **fal.ai LTX (Video):** ✅ Connected / ❌ No key — set FAL\_KEY
- **OpenRouter (Briefs):** ✅ Connected / ⚠️ Not configured

---

## Logging

All API requests, responses, status codes, and errors are logged to the terminal with timestamps.

Example terminal output:
```
22:15:03  INFO      [config]    API key status:
22:15:03  INFO      [config]      OpenRouter (text)    : ✓ configured
22:15:03  INFO      [config]      fal.ai (video)       : ✓ configured
22:15:03  INFO      [config]      Pollinations (image) : ✓ no key required
22:15:10  INFO      [image_gen] → [Pollinations AI] POST image request
22:15:10  INFO      [image_gen]   HEAD status  : 200
22:15:25  INFO      [video_gen] → [fal.ai] Submitting video generation request
22:15:25  INFO      [video_gen]   Model  : fal-ai/ltx-video
22:15:55  INFO      [video_gen] ← [fal.ai] Video URL: https://v3.fal.media/files/...
```

If video generation fails, the **exact provider error** is shown in the UI video card (not silently hidden).

---

## About the Models

### FLUX.1-dev (Image)
- Provider: **Pollinations AI** (`https://image.pollinations.ai`)
- Model: FLUX.1-dev from Black Forest Labs
- No API key required — publicly accessible endpoint
- Returns a direct image URL usable in `<img>` tags

### LTX-Video (Video)
- Provider: **fal.ai** (`fal-ai/ltx-video`)
- From Lightricks — fast, high-quality text-to-video
- Requires `FAL_KEY` (sign up at fal.ai)
- Generates ~5-second 512×512 videos from text prompts

---

## License

MIT
