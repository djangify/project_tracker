# assets/models.py
from django.db import models


class Asset(models.Model):
    """A piece of raw source material — an upload or pasted text — that can be
    fed into AI generation. Distinct from pages.Page, which stores structured
    *output* (notes/docs), not raw input."""

    FILE_TYPE_CHOICES = [
        ("text", "Text"),
        ("markdown", "Markdown"),
        ("pdf", "PDF"),
        ("image", "Image"),
        ("audio", "Audio"),
        ("video", "Video"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to="assets/",
        blank=True,
        null=True,
        help_text="Optional: upload the original file (PDF, doc, image, audio, etc.)",
    )
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default="text")
    content = models.TextField(
        blank=True,
        help_text="Pasted text/transcript, or text extracted from the uploaded file. "
        "This is what actually gets sent to the AI — the file itself is just for reference.",
    )
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated")
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )
    contact = models.ForeignKey(
        "crm.Contact",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )
    token_count = models.PositiveIntegerField(
        default=0, help_text="Rough estimate (chars / 4), for planning what fits in a prompt — not billing-accurate"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def save(self, *args, **kwargs):
        self.token_count = max(1, len(self.content) // 4) if self.content else 0
        super().save(*args, **kwargs)


class PromptTemplate(models.Model):
    """A reusable system prompt for a given kind of output, so prompts live in
    one place instead of being hardcoded into views."""

    CONTENT_TYPE_CHOICES = [
        ("blog", "Blog post"),
        ("social", "Social media"),
        ("email", "Email"),
        ("funnel", "Funnel / sales copy"),
        ("docs", "Documentation"),
        ("general", "General"),
    ]

    name = models.CharField(max_length=150)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default="general")
    system_prompt = models.TextField(help_text="Instructions given to the AI before your asset content")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["content_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_content_type_display()})"


class VoiceProfile(models.Model):
    """A distilled 'brand voice' derived from your own writing samples via one
    AI call. Single-user, so there's no per-project split — just whichever
    profile(s) you've built, with one marked active as the default."""

    SENTENCE_LENGTH_CHOICES = [
        ("short", "Short & punchy"),
        ("medium", "Medium"),
        ("long", "Long & flowing"),
        ("varied", "Varied"),
    ]

    name = models.CharField(max_length=150, default="My voice")
    summary = models.TextField(blank=True, help_text="One or two sentence summary of the voice")
    tone_words = models.JSONField(default=list, blank=True)
    sentence_length = models.CharField(max_length=10, choices=SENTENCE_LENGTH_CHOICES, default="varied")
    words_to_avoid = models.JSONField(default=list, blank=True)
    sample_paragraphs = models.JSONField(default=list, blank=True)
    do_notes = models.JSONField(default=list, blank=True)
    dont_notes = models.JSONField(default=list, blank=True)
    source_assets = models.ManyToManyField(Asset, blank=True, related_name="voice_profiles")
    is_active = models.BooleanField(
        default=True, help_text="Used as the default voice when generating content, if none is chosen explicitly"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class GenerationJob(models.Model):
    """Tracks one AI generation run: which assets + prompt template went in,
    what page came out. Runs synchronously for now — this model exists so
    there's a record of what was generated from what, and a place to grow
    into background processing later without changing the shape of the data."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    prompt_template = models.ForeignKey(
        PromptTemplate, on_delete=models.SET_NULL, null=True, related_name="jobs"
    )
    voice_profile = models.ForeignKey(
        VoiceProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs"
    )
    assets = models.ManyToManyField(Asset, related_name="generation_jobs")
    instructions = models.TextField(blank=True, help_text="Extra one-off instructions for this run")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True)
    result_page = models.ForeignKey(
        "pages.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="generation_job"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Generation job #{self.pk} ({self.status})"
