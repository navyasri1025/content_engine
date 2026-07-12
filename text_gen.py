"""Text generation module."""
import json
import re

from openai import OpenAI

from config import HAS_OPENROUTER, OPENROUTER_API_KEY, TEXT_MODEL

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            timeout=30,
        )
    return _client


def _call_llm(system_prompt, user_prompt, max_tokens=500):
    if not HAS_OPENROUTER:
        return None
    try:
        c = _get_client()
        r = c.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[text_gen] LLM call failed: {e}")
        return None

# --- Prompt 1: Tagline (Few-Shot) ---
FEW_SHOT_EXAMPLES = {
    "playful": [
        ("Product: Bubblicious Bubble Gum\nAudience: Kids aged 6-12",
         "Chew the fun, blow the bubble!"),
        ("Product: ZoomZoom Scooters\nAudience: Adventurous teens",
         "Go fast. Laugh louder."),
        ("Product: Happy Paws Pet Treats\nAudience: Dog owners",
         "Wag more, bark less!"),
    ],
    "premium": [
        ("Product: Noir Velvet Perfume\nAudience: Luxury collectors",
         "Elegance captured in every drop."),
        ("Product: Aurum Timepieces\nAudience: Wealthy professionals",
         "Time, redefined by precision."),
        ("Product: Silk Haven Bedding\nAudience: Hotel buyers",
         "Sleep on the finest threads."),
    ],
    "eco": [
        ("Product: GreenLeaf Reusable Bottles\nAudience: Eco-conscious millennials",
         "Sip from the future, save the planet."),
        ("Product: TerraWear Organic Cotton\nAudience: Sustainable fashion advocates",
         "Wear the change you wish to see."),
        ("Product: SunCharger Solar Panels\nAudience: Off-grid homeowners",
         "Harness the sun, power your life."),
    ],
    "professional": [
        ("Product: DataSync Cloud Platform\nAudience: Enterprise IT managers",
         "Seamless sync. Zero downtime."),
        ("Product: SecureVault Password Manager\nAudience: Cybersecurity teams",
         "Your security is our architecture."),
        ("Product: QuickLedger Accounting\nAudience: Small business owners",
         "Simplify your numbers, amplify your growth."),
    ],
}
FEW_SHOT_DEFAULT = FEW_SHOT_EXAMPLES["professional"]

TAGLINE_SYSTEM = """You are a world-class creative director. \
Your specialty is distilling a brand's essence into one powerful line.

Generate ONE campaign tagline that:
- Captures the product's core value proposition
- Resonates with the target audience
- Matches the brand tone exactly
- Is memorable and shareable
- Max 10 words
- No hashtags, no emojis
- Return ONLY the tagline text"""


def generate_tagline(product, audience, tone):
    tone = tone.lower().strip()
    examples = FEW_SHOT_EXAMPLES.get(tone, FEW_SHOT_DEFAULT)
    ex_text = "\n\n".join(
        f"Example {i+1}:\nContext: {ctx}\nTagline: \"{tag}\""
        for i, (ctx, tag) in enumerate(examples)
    )
    prompt = f"Here are examples of great taglines:\n\n{ex_text}\n\nNow generate a tagline for:\nProduct: {product}\nAudience: {audience}\nTone: {tone}\n\nMax 10 words. No hashtags. Return ONLY the tagline."
    result = _call_llm(TAGLINE_SYSTEM, prompt, 50)
    if result is None:
        return f"{product}: Built for {audience}"
    return result.strip('"\' \n')
# --- Prompt 2: Blog Intro (Role-Based) ---
BLOG_SYSTEM_TEMPLATE = """You are an expert content strategist with 15 years of experience \
writing for {audience}. You have been hired by {product} to craft the introduction \
to a flagship blog post.

Your writing must:
- Hook the reader in the first sentence
- Speak directly to {audience} using their language and pain points
- Weave in the campaign tagline naturally: "{tagline}"
- Build curiosity so the reader wants to continue reading
- Exactly 200 words (strict)
- Tone: {tone}
- No markdown formatting -- just flowing prose
- End with a smooth transition

Return ONLY the blog intro text."""


def generate_blog_intro(product, audience, tone, tagline):
    system_prompt = BLOG_SYSTEM_TEMPLATE.format(
        audience=audience, product=product, tagline=tagline, tone=tone,
    )
    user_prompt = f"""Write a 200-word blog introduction for {product}.

Product: {product}
Audience: {audience}
Tone: {tone}
Tagline: "{tagline}"
Title: "Why {product} Is Changing the Game for {audience}"

Exactly 200 words. Hook first sentence. Natural tagline integration. No markdown."""
    result = _call_llm(system_prompt, user_prompt, 400)
    if result is None:
        return (f"Imagine a world where {audience} have exactly what they need. "
                f"{tagline} In this post, we explore how {product} is transforming "
                f"the experience for {audience}, one innovation at a time.")
    return result
# --- Prompt 3: Social Posts (Structured Output) ---
SOCIAL_SYSTEM = """You are a social media marketing strategist. Create social posts.

Generate posts for THREE platforms:
- Twitter/X: Max 280 characters. Punchy, conversational.
- Instagram: Max 2200 characters. Visual, storytelling. Include 3-5 hashtags.
- LinkedIn: Max 700 characters. Professional, insightful, value-driven.

Return ONLY valid JSON. No markdown fences. No extra text.
Schema:
{
  "twitter": "string (max 280 chars)",
  "instagram": "string (max 2200 chars)",
  "linkedin": "string (max 700 chars)"
}"""


def generate_social_posts(product, audience, tone):
    user_prompt = f"""Create platform-specific social media posts for:

Product: {product}
Audience: {audience}
Tone: {tone}

Platform limits:
- Twitter: 280 chars max
- Instagram: 2200 chars max
- LinkedIn: 700 chars max

Return ONLY valid JSON."""
    result = _call_llm(SOCIAL_SYSTEM, user_prompt, 600)
    if result is None:
        return _fallback(product, audience)
    cleaned = result.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(
            l for l in cleaned.split("\n") if not l.strip().startswith("```")
        )
    cleaned = cleaned.strip()
    try:
        posts = json.loads(cleaned)
        if {"twitter", "instagram", "linkedin"}.issubset(posts.keys()):
            return posts
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if m:
        try:
            posts = json.loads(m.group())
            if {"twitter", "instagram", "linkedin"}.issubset(posts.keys()):
                return posts
        except json.JSONDecodeError:
            pass
    return _fallback(product, audience)


def _fallback(product, audience):
    tag = product.replace(" ", "")
    return {
        "twitter": f"Introducing {product} -- built for {audience}. #Innovation",
        "instagram": f"Something new is here.\n\nMeet {product} -- for {audience}.\n\n#NewLaunch #{tag} #Innovation",
        "linkedin": f"We're excited to introduce {product}, purpose-built for {audience}. #Innovation #{tag}",
    }