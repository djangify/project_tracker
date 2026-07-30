# assets/services.py
"""AI generation service for the assets app.

Turns one or more Assets (plus an optional VoiceProfile) into content, guided by
a PromptTemplate, and distils VoiceProfiles from their source assets.

Every model call goes through ai_settings.ai_client — the single, provider-
agnostic adapter (OpenAI / Anthropic / Gemini), configured in AI Settings with
the API key encrypted at rest. This module keeps its own GenerationError type so
the existing views/UX are unchanged; ai_client's config errors are translated
into it.
"""
import json
import re

from ai_settings import ai_client


class GenerationError(Exception):
    """Raised when the AI call can't be made or fails in an expected way
    (no active provider/key, bad response) — caught and shown to the user as a
    message rather than a 500."""


def _generate(system_prompt, user_prompt, temperature=0.7):
    try:
        return ai_client.generate(system_prompt, user_prompt, temperature)
    except ai_client.AIConfigError as exc:
        raise GenerationError(f"{exc} Set one up in AI Settings.") from exc


def _extract_json(raw):
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
    assets = list(job.assets.all())
    if not assets:
        raise GenerationError("This generation job has no assets attached.")

    user_prompt = build_prompt(assets, job.voice_profile, job.instructions)
    system_prompt = job.prompt_template.system_prompt if job.prompt_template else ""
    return _generate(system_prompt, user_prompt, temperature=0.7)


def distill_voice_profile(voice_profile):
    """One AI call that (re)distills a VoiceProfile from its source_assets' content."""
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
    raw = _generate(system_prompt, sample_text, temperature=0.4)
    data = _extract_json(raw)
    if not data:
        raise GenerationError("The AI didn't return valid JSON — try again.")

    voice_profile.summary = data.get("summary", "")
    voice_profile.tone_words = data.get("tone_words", [])
    voice_profile.sentence_length = data.get("sentence_length", "varied")
    voice_profile.words_to_avoid = data.get("words_to_avoid", [])
    voice_profile.sample_paragraphs = data.get("sample_paragraphs", [])
    voice_profile.do_notes = data.get("do_notes", [])
    voice_profile.dont_notes = data.get("dont_notes", [])
    voice_profile.save()
    return voice_profile
