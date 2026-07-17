# assets/services.py
"""AI generation service. Turns one or more Assets (plus an optional
VoiceProfile) into a piece of content, guided by a PromptTemplate — one
synchronous call to the Anthropic API. No background queue: if generation
calls start taking long enough to need one, this is the seam to add it at
(swap the body of generate_content for a task enqueue + GenerationJob poll).
"""
import json
import os

from django.conf import settings


class GenerationError(Exception):
    """Raised when the AI call can't be made or fails in an expected way
    (missing key, missing package, bad response) — caught and shown to the
    user as a message rather than a 500."""


def _site_config():
    """Lazy import to avoid a hard dependency on core at module load time."""
    from core.models import SiteConfiguration

    return SiteConfiguration.objects.filter(pk=1).first()


def _api_key():
    """The dashboard (Settings page) is the primary source — it's what works
    identically in the packaged desktop app and in dev. The environment
    variable is a fallback for local/server development only."""
    config = _site_config()
    if config and config.anthropic_api_key:
        return config.anthropic_api_key
    return getattr(settings, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")


def _model_name():
    config = _site_config()
    if config and config.anthropic_default_model:
        return config.anthropic_default_model
    return getattr(settings, "ANTHROPIC_DEFAULT_MODEL", "claude-sonnet-4-5")


def _client():
    api_key = _api_key()
    if not api_key:
        raise GenerationError(
            "No Anthropic API key configured. Add one in Settings (the gear icon in the sidebar) to enable AI generation."
        )
    try:
        import anthropic
    except ImportError as exc:
        raise GenerationError(
            "The 'anthropic' package isn't installed. Run: pip install anthropic"
        ) from exc
    return anthropic.Anthropic(api_key=api_key)


def build_prompt(assets, voice_profile=None, instructions=""):
    """Assemble the user-turn text sent to the model from assets + voice + one-off instructions."""
    parts = []
    if voice_profile:
        parts.append("BRAND VOICE:")
        if voice_profile.summary:
            parts.append(voice_profile.summary)
        if voice_profile.tone_words:
            parts.append("Tone words: " + ", ".join(voice_profile.tone_words))
        if voice_profile.sentence_length:
            parts.append(f"Sentence length: {voice_profile.get_sentence_length_display()}")
        if voice_profile.do_notes:
            parts.append("Do: " + "; ".join(voice_profile.do_notes))
        if voice_profile.dont_notes:
            parts.append("Don't: " + "; ".join(voice_profile.dont_notes))
        parts.append("")

    parts.append("SOURCE MATERIAL:")
    for asset in assets:
        parts.append(f"--- {asset.title} ---")
        parts.append(asset.content or "(no extracted text content for this asset)")
    parts.append("")

    if instructions:
        parts.append("ADDITIONAL INSTRUCTIONS:")
        parts.append(instructions)

    return "\n".join(parts)


def generate_content(job):
    """Run a GenerationJob synchronously and return the generated text.
    Does not create the Page — the caller decides what to do with the result."""
    client = _client()
    assets = list(job.assets.all())
    if not assets:
        raise GenerationError("This generation job has no assets attached.")

    user_prompt = build_prompt(assets, job.voice_profile, job.instructions)
    system_prompt = job.prompt_template.system_prompt if job.prompt_template else ""

    response = client.messages.create(
        model=_model_name(),
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


def distill_voice_profile(voice_profile):
    """One AI call that (re)distills a VoiceProfile from its source_assets' content."""
    client = _client()
    assets = list(voice_profile.source_assets.all())
    if not assets:
        raise GenerationError("Add at least one source asset before distilling a voice profile.")

    sample_text = "\n\n---\n\n".join(a.content for a in assets if a.content)
    if not sample_text.strip():
        raise GenerationError("The source assets have no extracted text content to learn from.")

    system_prompt = (
        "You analyze writing samples and return a JSON object describing the author's voice. "
        "Return ONLY valid JSON with keys: summary (string), tone_words (list of strings), "
        "sentence_length (one of short/medium/long/varied), words_to_avoid (list of strings), "
        "sample_paragraphs (list of 2-3 short paragraphs distilled from the samples), "
        "do_notes (list of strings), dont_notes (list of strings). No prose outside the JSON."
    )
    response = client.messages.create(
        model=_model_name(),
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": sample_text}],
    )
    raw = response.content[0].text
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GenerationError("The AI didn't return valid JSON — try again.") from exc

    voice_profile.summary = data.get("summary", "")
    voice_profile.tone_words = data.get("tone_words", [])
    voice_profile.sentence_length = data.get("sentence_length", "varied")
    voice_profile.words_to_avoid = data.get("words_to_avoid", [])
    voice_profile.sample_paragraphs = data.get("sample_paragraphs", [])
    voice_profile.do_notes = data.get("do_notes", [])
    voice_profile.dont_notes = data.get("dont_notes", [])
    voice_profile.save()
    return voice_profile
