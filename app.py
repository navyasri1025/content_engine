"""
AI Content Engine -- Streamlit App.

One brief in -> five creative assets out.
"""

import logging
import time

import streamlit as st

from config import HAS_OPENROUTER, HAS_VIDEO
from text_gen import generate_tagline, generate_blog_intro, generate_social_posts
from image_gen import generate_image
from video_gen import generate_video, generate_video_brief, generate_audio_script

# ── Logger ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("app")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Content Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "generated" not in st.session_state:
    st.session_state.generated = False
if "results" not in st.session_state:
    st.session_state.results = {}
if "running" not in st.session_state:
    st.session_state.running = False

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Design tokens ───────────────────────────────────────────────────────── */
:root {
    --bg-app:    linear-gradient(160deg, #0d1117 0%, #161b22 100%);
    --bg-card:   #161b22;
    --c-border:  #30363d;
    --c-text1:   #e6edf3;
    --c-text2:   #c9d1d9;
    --c-text3:   #8b949e;   /* raised from #6e7681 — better contrast on dark bg */
    --c-placeholder: #8b949e;
}

/* ── Font — target named containers only, never [data-testid] wholesale      */
/* (blanket [data-testid] selector clips st.status() text — do NOT restore)  */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
[data-testid="stMainBlockContainer"],
[data-testid="column"] { font-family: 'Inter', sans-serif !important; }

/* ── App background & chrome ─────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: var(--bg-app) !important; }
[data-testid="stHeader"]           { background: transparent !important; }
.block-container                   { padding-top: 1.5rem; }

/* ── Typography ──────────────────────────────────────────────────────────── */
h1, h2, h3, .stMarkdown { color: var(--c-text1) !important; }

/* ── Sidebar form — labels ───────────────────────────────────────────────── */
.stTextInput  label,
.stSelectbox  label { color: var(--c-text2) !important; font-weight: 500 !important; }

/* ── Placeholder text — high-contrast for dark mode ─────────────────────── */
/* Targets the real <input> placeholder inside Streamlit's shadow DOM        */
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder { color: var(--c-placeholder) !important; opacity: 1 !important; }

/* ── Sidebar form — field spacing ───────────────────────────────────────── */
/* Add breathing room between each form row so fields don't crowd the button */
[data-testid="stSidebar"] .stTextInput,
[data-testid="stSidebar"] .stSelectbox { margin-bottom: 0.75rem !important; }

/* ── Generate Campaign button ────────────────────────────────────────────── */
[data-testid="stSidebar"] .stFormSubmitButton > button,
.stButton > button {
    width: 100% !important;
    background: #3b82f6 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em !important;
    margin-top: 0.5rem !important;   /* gap above button inside form */
    transition: background 0.15s ease, opacity 0.15s ease !important;
}
[data-testid="stSidebar"] .stFormSubmitButton > button:hover,
.stButton > button:hover { background: #2563eb !important; }

/* Loading state — while pipeline is running the button is disabled          */
[data-testid="stSidebar"] .stFormSubmitButton > button:disabled,
.stButton > button:disabled {
    background: #1e3a5f !important;
    color: #6b7280 !important;
    cursor: not-allowed !important;
    opacity: 0.75 !important;
}

/* ── Content cards — consistent padding & margins ────────────────────────── */
.card {
    background:    var(--bg-card);
    border:        1px solid var(--c-border);
    border-radius: 12px;
    padding:       1.25rem 1.25rem 1rem 1.25rem;
    margin-bottom: 1rem;
    /* prevent content overflow from clipping text inside cards */
    overflow: visible;
    word-break: break-word;
}
.card-title {
    font-size:      0.72rem;
    font-weight:    600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color:          var(--c-text3);
    margin-bottom:  0.5rem;
    /* explicit overflow rules — no clip */
    overflow: visible;
    white-space: normal;
}
.card-content {
    color:       var(--c-text1);
    font-size:   0.95rem;
    line-height: 1.6;
    overflow:    visible;
    white-space: normal;
}

/* ── Error / warning callouts ────────────────────────────────────────────── */
.card-error {
    color:      #f87171;
    font-size:  0.82rem;
    font-family: monospace;
    background: rgba(248,113,113,0.08);
    border:     1px solid rgba(248,113,113,0.25);
    border-radius: 6px;
    padding:    0.5rem 0.75rem;
    margin-top: 0.5rem;
    white-space: pre-wrap;
    word-break:  break-word;
}
.card-warn {
    color:      #fbbf24;
    font-size:  0.82rem;
    font-family: monospace;
    background: rgba(251,191,36,0.08);
    border:     1px solid rgba(251,191,36,0.25);
    border-radius: 6px;
    padding:    0.5rem 0.75rem;
    margin-top: 0.5rem;
    white-space: pre-wrap;
    word-break:  break-word;
}

/* ── Technique badges ────────────────────────────────────────────────────── */
.technique-badge {
    display:       inline-block;
    font-size:     0.65rem;
    font-weight:   600;
    padding:       0.15rem 0.5rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
    white-space:   nowrap;
}
.badge-blue   { background: rgba(59,130,246,0.12); color: #3b82f6; }
.badge-green  { background: rgba(34,197,94,0.12);  color: #22c55e; }
.badge-purple { background: rgba(168,85,247,0.12); color: #a855f7; }
.badge-orange { background: rgba(249,115,22,0.12); color: #f97316; }
.badge-teal   { background: rgba(20,184,166,0.12); color: #14b8a6; }

/* ── Responsive — 1366×768 guard: prevent column overflow ───────────────── */
@media (max-width: 1400px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .card { padding: 1rem !important; }
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state {
    display:         flex;
    flex-direction:  column;
    align-items:     center;
    justify-content: center;
    padding:         4rem 1rem 3rem;
    text-align:      center;
    color:           #8b949e;
    font-size:       1.05rem;
    line-height:     1.6;
}
.empty-state-icon {
    font-size:     2.8rem;
    margin-bottom: 0.75rem;
    opacity:       0.85;
}
.empty-state-text {
    color:       #c9d1d9;
    font-size:   1.1rem;
    font-weight: 500;
    max-width:   480px;
}
</style>
""", unsafe_allow_html=True)

# ── Disable browser autocomplete on sidebar text inputs ───────────────────────
# Also hides the "Press Enter to submit form" tooltip Streamlit injects, and
# suppresses Enter-key submission inside the two text fields.
st.markdown("""
<style>
/* Hide Streamlit's "Press Enter to submit form" tooltip on all text inputs */
[data-testid="InputInstructions"] { display: none !important; }
</style>
<script>
(function patchSidebarInputs() {
    function patch() {
        document.querySelectorAll('input[aria-label="Product Name"], input[aria-label="Target Audience"]')
            .forEach(function(el) {
                /* Autocomplete / autofill suppression */
                el.setAttribute('autocomplete', 'off');
                el.setAttribute('autocorrect', 'off');
                el.setAttribute('autocapitalize', 'off');
                el.setAttribute('spellcheck', 'false');

                /* Prevent Enter from submitting the form — only if not already patched */
                if (!el.dataset.enterPatched) {
                    el.dataset.enterPatched = '1';
                    el.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            e.stopPropagation();
                        }
                    }, true);
                }
            });
    }
    patch();
    setTimeout(patch, 500);
    setTimeout(patch, 1500);
})();
</script>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Campaign Brief")
    with st.form("brief_form"):
        product_name    = st.text_input("Product Name",    placeholder="e.g. EcoWave Water Bottle")
        target_audience = st.text_input("Target Audience", placeholder="e.g. Eco-conscious millennials")
        brand_tone      = st.selectbox("Brand Tone", ["professional", "playful", "premium", "eco"], index=0)
        submitted = st.form_submit_button(
            "⏳ Generating…" if st.session_state.running else "🚀 Generate Campaign",
            use_container_width=True,
            disabled=st.session_state.running,
        )

# ── Main header ───────────────────────────────────────────────────────────────
st.markdown("# 🎬 AI Content Engine")
st.markdown("### One brief → five creative assets")

if not HAS_OPENROUTER:
    st.warning("⚠️ OpenRouter API key not found. Add `OPENROUTER_API_KEY` to `.env` for full functionality.")


# ── Generation pipeline ───────────────────────────────────────────────────────
def run_generation(product: str, audience: str, tone: str) -> None:
    st.session_state.running  = True
    st.session_state.generated = False
    results: dict = {}

    try:
        # ── Step 1: Tagline ───────────────────────────────────────────────────
        with st.status("Step 1/5: Generating tagline…", expanded=True) as s:
            time.sleep(0.2)
            logger.info("=== Step 1/5: Tagline ===")
            tagline = generate_tagline(product, audience, tone)
            results["tagline"] = tagline
            results["tagline_technique"] = "Few-Shot Prompting"
            s.update(label=f'Tagline: "{tagline}"', state="complete", expanded=False)

        # ── Step 2: Blog intro ────────────────────────────────────────────────
        with st.status("Step 2/5: Writing blog intro…", expanded=True) as s:
            time.sleep(0.2)
            logger.info("=== Step 2/5: Blog intro ===")
            blog = generate_blog_intro(product, audience, tone, tagline)
            results["blog"] = blog
            results["blog_technique"] = "Role-Based Prompting"
            s.update(label="Blog intro written", state="complete", expanded=False)

        # ── Step 3: Social posts ──────────────────────────────────────────────
        with st.status("Step 3/5: Creating social posts…", expanded=True) as s:
            time.sleep(0.2)
            logger.info("=== Step 3/5: Social posts ===")
            social = generate_social_posts(product, audience, tone)
            results["social"] = social
            results["social_technique"] = "Structured Output"
            s.update(label="Social posts created", state="complete", expanded=False)

        # ── Step 4: Hero image ────────────────────────────────────────────────
        with st.status("Step 4/5: Generating hero image (FLUX.1-dev)…", expanded=True) as s:
            time.sleep(0.2)
            logger.info("=== Step 4/5: Hero image ===")
            image_url = generate_image(product, tagline, tone)
            results["image_url"] = image_url
            results["image_technique"] = "Pollinations FLUX.1-dev"
            if image_url:
                s.update(label="Hero image generated ✓", state="complete", expanded=False)
            else:
                s.update(label="Image generation failed — see terminal", state="error", expanded=False)

        # ── Step 5: Video brief + audio script + Ken Burns video ──────────────
        with st.status("Step 5/5: Generating video brief, voiceover & Ken Burns video…", expanded=True) as s:
            time.sleep(0.2)
            logger.info("=== Step 5/5: Video brief + audio script + Ken Burns video ===")

            # Generate text-based brief and voiceover script via OpenRouter
            video_brief  = None
            audio_script = None
            if HAS_VIDEO:
                video_brief  = generate_video_brief(product, tagline, tone, audience)
                audio_script = generate_audio_script(product, tagline, tone)

            # Extract voiceover text (used as narration for the video)
            tts_script: str | None = None
            if audio_script and isinstance(audio_script, dict):
                tts_script = audio_script.get("script")

            # Build the local Ken Burns video (always runs — no API key needed)
            video_path, video_error = generate_video(
                product=product,
                tagline=tagline,
                tone=tone,
                audience=audience,
                image_url=image_url,
                voiceover_script=tts_script,
            )

            results["video_path"]            = video_path
            results["video_error"]           = video_error
            results["video_technique"]       = "Ken Burns (local) + Edge TTS"
            results["video_brief"]           = video_brief
            results["video_brief_technique"] = "OpenRouter Video Brief"
            results["audio_script"]          = audio_script
            results["audio_technique"]       = "OpenRouter Voiceover Script"

            if video_path:
                s.update(label="Ken Burns video generated ✓", state="complete", expanded=False)
            elif video_error:
                s.update(label=f"Video failed: {video_error[:60]}…", state="error", expanded=False)
            else:
                s.update(label="Video generation skipped", state="complete", expanded=False)

    except Exception as exc:
        logger.error("Pipeline error: %s", exc, exc_info=True)
        st.error(f"Pipeline failed: {exc}")

    st.session_state.results   = results
    st.session_state.generated = True
    st.session_state.running   = False


if submitted and product_name:
    run_generation(product_name.strip(), target_audience.strip(), brand_tone)
    st.rerun()


# ── Results display ───────────────────────────────────────────────────────────
if st.session_state.generated and st.session_state.results:
    results = st.session_state.results
    col1, col2 = st.columns([1, 1], gap="large")

    # ── Left: Text assets ─────────────────────────────────────────────────────
    with col1:
        st.markdown("## 📝 Text Assets")

        tagline = results.get("tagline", "")
        if tagline:
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-blue">{results.get('tagline_technique', 'Few-Shot')}</span>
                <div class="card-title">🏷️ Campaign Tagline</div>
                <div class="card-content" style="font-size:1.2rem;font-weight:600;font-style:italic;">"{tagline}"</div>
            </div>""", unsafe_allow_html=True)

        blog = results.get("blog", "")
        if blog:
            wc = len(blog.split())
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-green">{results.get('blog_technique', 'Role-Based')}</span>
                <div class="card-title">📖 Blog Intro ({wc} words)</div>
                <div class="card-content">{blog}</div>
            </div>""", unsafe_allow_html=True)

        social = results.get("social", {})
        if social:
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-purple">{results.get('social_technique', 'Structured Output')}</span>
                <div class="card-title">📱 Social Media Posts</div>
            </div>""", unsafe_allow_html=True)
            for platform, icon, limit in [
                ("twitter",   "🐦 Twitter/X",  280),
                ("instagram", "📸 Instagram",  2200),
                ("linkedin",  "💼 LinkedIn",    700),
            ]:
                text = social.get(platform, "")
                if text:
                    cc = len(text)
                    st.markdown(f"""<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem;">
                        <div style="font-size:0.7rem;font-weight:600;color:#6e7681;text-transform:uppercase;margin-bottom:0.25rem;">
                            {icon} <span style="font-weight:400;text-transform:none;">({cc}/{limit} chars)</span>
                        </div>
                        <div style="color:#e6edf3;font-size:0.9rem;white-space:pre-line;">{text}</div>
                    </div>""", unsafe_allow_html=True)

    # ── Right: Visual assets ──────────────────────────────────────────────────
    with col2:
        st.markdown("## 🎨 Visual Assets")

        # Hero image
        image_url = results.get("image_url")
        if image_url:
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-orange">{results.get('image_technique', 'Pollinations FLUX.1-dev')}</span>
                <div class="card-title">🖼️ Campaign Hero Image (FLUX.1-dev)</div>
            </div>""", unsafe_allow_html=True)
            st.image(image_url, use_container_width=True)
        else:
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-orange">{results.get('image_technique', 'Pollinations FLUX.1-dev')}</span>
                <div class="card-title">🖼️ Campaign Hero Image (FLUX.1-dev)</div>
                <div class="card-content" style="color:#6e7681;">Image generation failed. Check terminal logs for the exact error.</div>
            </div>""", unsafe_allow_html=True)

        # Ken Burns video
        video_path  = results.get("video_path")
        video_error = results.get("video_error")

        if video_path:
            # Decide badge colour: teal if fully successful, orange if warning (silent fallback)
            badge_cls = "badge-teal" if not video_error else "badge-orange"
            st.markdown(f"""<div class="card">
                <span class="technique-badge {badge_cls}">{results.get('video_technique', 'Ken Burns + Edge TTS')}</span>
                <div class="card-title">🎬 Promo Video (Ken Burns + Edge TTS)</div>
            </div>""", unsafe_allow_html=True)
            # Warn if audio fell back
            if video_error:
                escaped_warn = video_error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                st.markdown(f'<div class="card-warn">⚠️ {escaped_warn}</div>', unsafe_allow_html=True)
            try:
                st.video(video_path)
            except Exception:
                st.markdown(
                    f"<div class='card-content'>Video saved: <code>{video_path}</code></div>",
                    unsafe_allow_html=True,
                )
            # Download button
            try:
                with open(video_path, "rb") as vf:
                    st.download_button(
                        label="⬇️ Download MP4",
                        data=vf.read(),
                        file_name="campaign_video.mp4",
                        mime="video/mp4",
                    )
            except Exception:
                pass
        else:
            error_html = ""
            if video_error:
                escaped = video_error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                error_html = f'<div class="card-error"><strong>Error:</strong> {escaped}</div>'
            st.markdown(f"""<div class="card"><span class="technique-badge badge-teal">{results.get('video_technique', 'Ken Burns + Edge TTS')}</span><div class="card-title">🎬 Promo Video (Ken Burns + Edge TTS)</div>{error_html}</div>""", unsafe_allow_html=True)

        # Video creative brief
        video_brief = results.get("video_brief")
        if video_brief:
            title = video_brief.get("title", "Promo Video Concept")
            shots = video_brief.get("shots", [])
            music = video_brief.get("music_direction", "")
            cta   = video_brief.get("call_to_action", "")
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-blue">{results.get('video_brief_technique', 'OpenRouter Video Brief')}</span>
                <div class="card-title">🎬 Video Creative Brief</div>
                <div class="card-content"><strong>Title:</strong> {title}</div>
                <div class="card-content" style="margin-top:0.5rem;"><strong>Shots:</strong></div>
            </div>""", unsafe_allow_html=True)
            for shot in shots[:4]:
                sn   = shot.get("shot_number", "?")
                desc = shot.get("description", "")
                cam  = shot.get("camera", "")
                dur  = shot.get("duration_seconds", "?")
                st.markdown(f"""<div style="background:#1c2128;border:1px solid #30363d;border-radius:6px;padding:0.5rem 0.75rem;margin-bottom:0.5rem;">
                    <div style="font-size:0.75rem;font-weight:600;color:#8b949e;">Shot {sn} ({dur}s)</div>
                    <div style="color:#e6edf3;font-size:0.85rem;">{desc}</div>
                    <div style="color:#6e7681;font-size:0.75rem;font-style:italic;">Camera: {cam}</div>
                </div>""", unsafe_allow_html=True)
            if music:
                st.markdown(f'<div style="color:#c9d1d9;font-size:0.85rem;margin-bottom:0.25rem;"><strong>Music:</strong> {music}</div>', unsafe_allow_html=True)
            if cta:
                st.markdown(f'<div style="color:#c9d1d9;font-size:0.85rem;margin-bottom:0.5rem;"><strong>CTA:</strong> {cta}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="card"><span class="technique-badge badge-blue">{results.get('video_brief_technique', 'OpenRouter Video Brief')}</span><div class="card-title">🎬 Video Creative Brief</div><div class="card-content" style="color:#6e7681;">Not generated — set <code>OPENROUTER_API_KEY</code> in <code>.env</code>.</div></div>""", unsafe_allow_html=True)

        # Audio voiceover script
        audio_script = results.get("audio_script")
        if audio_script:
            script     = audio_script.get("script", "")
            tone_guide = audio_script.get("tone_guide", "")
            st.markdown(f"""<div class="card">
                <span class="technique-badge badge-green">{results.get('audio_technique', 'OpenRouter Voiceover')}</span>
                <div class="card-title">🎙️ Audio Voiceover Script</div>
                <div class="card-content" style="font-style:italic;">"{script}"</div>
                <div class="card-content" style="color:#6e7681;font-size:0.8rem;margin-top:0.25rem;">Tone: {tone_guide}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="card"><span class="technique-badge badge-green">{results.get('audio_technique', 'OpenRouter Voiceover')}</span><div class="card-title">🎙️ Audio Voiceover Script</div><div class="card-content" style="color:#6e7681;">Not generated — set <code>OPENROUTER_API_KEY</code> in <code>.env</code>.</div></div>""", unsafe_allow_html=True)

# ── Empty state ───────────────────────────────────────────────────────────────
elif not st.session_state.generated and not st.session_state.running:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">✨</div>
        <div class="empty-state-text">Generate a campaign to create AI-powered marketing assets.</div>
    </div>
    """, unsafe_allow_html=True)

