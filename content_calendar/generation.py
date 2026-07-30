# content_calendar/generation.py
"""Content generation engine.

Ported/adapted from ai-marketing's content_generation + content_templates:
  - PromptEnhancer: prompt layering (content-type system prompt + voice profile)
  - distill_voice(): turn writing samples into a structured VoiceProfile
  - generate_content_item(): run a template (ordered per-field prompts) or a
    free-text brief and land the result in a draft ContentItem.

Every model call goes through ai_settings.ai_client.generate() so the engine is
provider-agnostic — it never imports openai/anthropic/google directly.
"""
import json
import re

from ai_settings import ai_client

from .models import ContentItem, VoiceProfile


# ---------------------------------------------------------------------------
# Prompt layering (adapted from prompt_enhancement.PromptEnhancer)
# ---------------------------------------------------------------------------
class PromptEnhancer:
    """Builds the (system_prompt, user_prompt) pair sent to the active provider.

    Unlike the OpenAI-only original, this returns a tuple for
    ai_client.generate() rather than an OpenAI `messages` list, and layers in
    the distilled voice profile when one is enabled.
    """

    GENERAL_TEMPLATE = (
        "You are a professional content creator. Write high-quality, natural, "
        "engaging content that matches the requested platform and tone. Use short "
        "sentences and active voice. Never use emojis unless explicitly asked. "
        "Return only the requested content with no preamble or explanation."
    )

    SOCIAL_TEMPLATE = (
        "You are a social media content creator. Write concise, authentic content "
        "for the specified platform, with a strong hook and a clear call to action "
        "where appropriate. Keep it punchy and scroll-stopping. Return only the "
        "requested content with no preamble or explanation."
    )

    BLOG_TEMPLATE = (
        "You are a blog content creator. Write a clear, well-structured piece with "
        "an engaging opening, short paragraphs, and markdown headings where useful. "
        "Return only the requested content with no preamble or explanation."
    )

    EMAIL_TEMPLATE = (
        "You are an email marketing specialist. Write a concise, scannable email "
        "with a compelling opening and a clear call to action. Return only the "
        "requested content with no preamble or explanation."
    )

    TEMPLATES = {
        "general": GENERAL_TEMPLATE,
        "social": SOCIAL_TEMPLATE,
        "blog": BLOG_TEMPLATE,
        "email": EMAIL_TEMPLATE,
    }

    # Map ContentItem content types onto the prompt categories above. This is a
    # social content calendar, so post formats default to the social template.
    CONTENT_TYPE_CATEGORY = {
        "reel": "social",
        "carousel": "social",
        "single_image": "social",
        "story": "social",
        "video": "social",
        "live": "social",
        "text": "social",
    }

    @classmethod
    def category_for(cls, content_type: str) -> str:
        """Resolve a ContentItem content type (or a raw category) to a prompt
        category. Falls back to 'social' for this app's domain."""
        if content_type in cls.TEMPLATES:
            return content_type
        return cls.CONTENT_TYPE_CATEGORY.get(content_type, "social")

    @classmethod
    def detect_content_type(cls, text: str) -> str:
        t = (text or "").lower()
        if any(kw in t for kw in ["blog", "article"]):
            return "blog"
        if any(kw in t for kw in ["email", "newsletter", "subject line"]):
            return "email"
        if any(kw in t for kw in ["reel", "story", "carousel", "caption", "hook",
                                  "hashtag", "instagram", "tiktok", "social", "post"]):
            return "social"
        return "general"

    @classmethod
    def voice_block(cls, voice: VoiceProfile | None) -> str:
        """Render the distilled voice profile as system-prompt guidance."""
        if not voice or not voice.enabled or not voice.is_distilled:
            return ""
        parts = ["\n\nWrite in this specific brand voice:"]
        if voice.summary:
            parts.append(f"- Voice: {voice.summary}")
        if voice.tone_words:
            parts.append(f"- Tone: {', '.join(voice.tone_words)}")
        if voice.sentence_length:
            parts.append(f"- Sentence length: {voice.get_sentence_length_display()}")
        if voice.words_to_avoid:
            parts.append(f"- Never use: {', '.join(voice.words_to_avoid)}")
        for note in voice.do_notes:
            parts.append(f"- Do: {note}")
        for note in voice.dont_notes:
            parts.append(f"- Don't: {note}")
        return "\n".join(parts)

    @classmethod
    def build(cls, user_prompt: str, content_type: str = "general",
              context: str = "", voice: VoiceProfile | None = None) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) for ai_client.generate()."""
        key = content_type if content_type in cls.TEMPLATES else "general"
        system = cls.TEMPLATES[key] + cls.voice_block(voice)

        user = user_prompt
        if context:
            user = f"{user_prompt}\n\nContext so far (stay consistent with this):\n{context}"
        return system, user


# ---------------------------------------------------------------------------
# Voice distillation (adapted from services.distill_voice)
# ---------------------------------------------------------------------------
VOICE_DISTILL_SYSTEM = """You are a brand-voice analyst. Read the writing \
samples below and distill the author's distinctive writing voice into a \
structured profile.

Return ONLY valid JSON with exactly these keys:
{
  "summary": "one or two sentence description of the voice",
  "tone_words": ["5-8 adjectives that describe the tone"],
  "sentence_length": "one of: short, medium, long, varied",
  "words_to_avoid": ["words or phrases this author would clearly never use"],
  "sample_paragraphs": ["2-3 short paragraphs written in the author's voice"],
  "do_notes": ["concrete do's for writing in this voice"],
  "dont_notes": ["concrete don'ts for writing in this voice"]
}

Base every field strictly on evidence in the samples. Do not invent \
biographical facts about the author. If the samples are thin, keep the \
profile modest rather than fabricating detail."""


def _extract_json(raw: str) -> dict:
    """Parse a JSON object out of a model reply, tolerating markdown fences."""
    if not raw:
        return {}
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    candidate = fenced.group(1) if fenced else raw
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        brace = re.search(r"\{.*\}", candidate, re.DOTALL)
        if brace:
            try:
                return json.loads(brace.group(0))
            except json.JSONDecodeError:
                return {}
        return {}


_VALID_SENTENCE_LENGTHS = {"short", "medium", "long", "varied"}


def distill_voice(sample_text: str, temperature: float = 0.4) -> VoiceProfile:
    """Distill writing samples into the singleton VoiceProfile and save it."""
    raw = ai_client.generate(VOICE_DISTILL_SYSTEM,
                             f"Writing samples:\n\n{sample_text}", temperature)
    data = _extract_json(raw)

    voice = VoiceProfile.get_solo()
    voice.summary = data.get("summary", "") or ""
    voice.tone_words = data.get("tone_words", []) or []
    sentence_length = (data.get("sentence_length") or "varied").lower()
    voice.sentence_length = sentence_length if sentence_length in _VALID_SENTENCE_LENGTHS else "varied"
    voice.words_to_avoid = data.get("words_to_avoid", []) or []
    voice.sample_paragraphs = data.get("sample_paragraphs", []) or []
    voice.do_notes = data.get("do_notes", []) or []
    voice.dont_notes = data.get("dont_notes", []) or []
    voice.raw_response = raw
    voice.mark_distilled()
    voice.save()
    return voice


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------
BRIEF_SYSTEM = """You are a social content creator. From the brief, produce one \
ready-to-post piece of content.

Return ONLY valid JSON with exactly these keys:
{
  "topic": "a short topic/title",
  "hook": "a scroll-stopping opening line",
  "caption": "the main caption/body",
  "call_to_action": "a single clear call to action",
  "hashtags": "a space-separated set of relevant hashtags"
}
Return only the JSON, no preamble."""


def _apply_voice_to_system(system: str) -> str:
    return system + PromptEnhancer.voice_block(VoiceProfile.objects.filter(pk=1).first())


def generate_from_brief(brief: str, content_type: str = "", temperature: float = 0.7) -> dict:
    """One structured call producing all ContentItem text fields from a brief."""
    system = _apply_voice_to_system(BRIEF_SYSTEM)
    raw = ai_client.generate(system, f"Brief:\n\n{brief}", temperature)
    return _extract_json(raw)


def generate_from_template(template, brief: str = "", temperature: float = 0.7) -> dict:
    """Run a template's prompts in order, feeding each result forward, and
    return a dict of {ContentItem field: generated value}."""
    voice = VoiceProfile.objects.filter(pk=1).first()
    content_type = PromptEnhancer.category_for(template.content_type)
    keywords = f"\n\nKeywords to weave in: {template.keywords}" if template.keywords else ""

    results: dict[str, str] = {}
    context_bits = []
    if brief:
        context_bits.append(f"Brief: {brief}")

    for step in template.prompts.all():
        instruction = f"{step.prompt}{keywords}"
        if brief and not context_bits:
            instruction = f"Brief: {brief}\n\n{instruction}"
        system, user = PromptEnhancer.build(
            instruction, content_type=content_type,
            context="\n".join(context_bits), voice=voice,
        )
        value = (ai_client.generate(system, user, temperature) or "").strip()
        results[step.target_field] = value
        context_bits.append(f"{step.get_target_field_display()}: {value}")

    return results


def generate_content_item(*, template=None, brief: str = "", scheduled_date=None,
                          project=None, content_type: str = "",
                          temperature: float = 0.7) -> ContentItem:
    """Create a draft ContentItem (approval_status='ready') from a template or
    a free-text brief, using whichever AI provider is active."""
    fields = {
        "topic": "", "hook": "", "caption": "", "call_to_action": "", "hashtags": "",
    }

    if template is not None:
        fields.update(generate_from_template(template, brief=brief, temperature=temperature))
        item_content_type = template.content_type or content_type
    else:
        fields.update(generate_from_brief(brief, content_type=content_type, temperature=temperature))
        item_content_type = content_type

    item = ContentItem.objects.create(
        project=project,
        scheduled_date=scheduled_date,
        content_type=item_content_type or "",
        topic=fields.get("topic", "")[:200],
        hook=fields.get("hook", ""),
        caption=fields.get("caption", ""),
        call_to_action=fields.get("call_to_action", "")[:255],
        hashtags=fields.get("hashtags", ""),
        status="draft",
        approval_status="ready",
    )
    if template is not None:
        platforms = list(template.default_platforms.all())
        if platforms:
            item.platforms.set(platforms)
    return item
