# content_calendar/models.py
from django.db import models
from django.utils import timezone

from projects.models import Project


class Platform(models.Model):
    """A social platform a content item can be published to.

    Kept as its own table (rather than six booleans on ContentItem) so adding a
    new platform later is a data change, not a migration. Seeded with the common
    ones in the initial data migration.
    """

    name = models.CharField(max_length=50, unique=True)
    order = models.IntegerField(default=0, help_text="Sort order in pickers/lists")

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ContentItem(models.Model):
    """One piece of scheduled content — mirrors the columns of the content
    planning spreadsheet, plus a workflow/approval status so items can move from
    idea → published and be reviewed before they go out.
    """

    # Where an item sits in the production pipeline.
    STATUS_CHOICES = [
        ("idea", "Idea"),
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    # The review gate. The generation engine (Phase 3) creates items as "ready".
    APPROVAL_STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ready", "Ready for Approval"),
        ("approved", "Approved"),
        ("changes", "Needs Changes"),
    ]

    # Common post formats. Blank allowed so it never blocks entering an item.
    CONTENT_TYPE_CHOICES = [
        ("reel", "Reel / Short"),
        ("carousel", "Carousel"),
        ("single_image", "Single image"),
        ("story", "Story"),
        ("video", "Video"),
        ("live", "Live"),
        ("text", "Text / Thread"),
    ]

    # Optional link to a business/project, so a content item can be tied to one
    # of several things you track. Null = general content.
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_items",
        help_text="Optional: the business/project this content is for",
    )

    scheduled_date = models.DateField(
        null=True, blank=True, help_text="The day this content is planned to go out"
    )
    pillar = models.CharField(
        max_length=100, blank=True, help_text="Content pillar / theme (free text)"
    )
    content_type = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES, blank=True
    )
    topic = models.CharField(max_length=200, blank=True)

    platforms = models.ManyToManyField(
        Platform, blank=True, related_name="content_items"
    )

    hook = models.TextField(blank=True, help_text="Opening line / scroll-stopper")
    caption = models.TextField(blank=True)
    call_to_action = models.CharField(max_length=255, blank=True)
    hashtags = models.TextField(blank=True)
    tags_links = models.TextField(blank=True, help_text="Accounts to tag, links to include")
    audio_sound = models.CharField(max_length=255, blank=True, help_text="Audio/sound to use")
    image_video_cover = models.FileField(
        upload_to="content_calendar/", null=True, blank=True,
        help_text="Cover image or video file",
    )
    content_link = models.URLField(blank=True, help_text="Published URL, once live")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="idea")
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS_CHOICES, default="draft"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.topic or self.hook[:50] or f"Content #{self.pk}"

    @property
    def is_overdue(self):
        return (
            self.scheduled_date is not None
            and self.status not in ("published", "archived")
            and self.scheduled_date < timezone.localdate()
        )


# ---------------------------------------------------------------------------
# Generation engine (Phase 3) — ported/adapted from ai-marketing
# ---------------------------------------------------------------------------
class VoiceProfile(models.Model):
    """A structured 'brand voice' distilled from writing samples via one AI call.

    Single-user, so this is a singleton (get via `VoiceProfile.get_solo()`).
    When enabled and distilled, the generation engine layers it into the system
    prompt so generated content sounds like the owner.
    Ported from ai-marketing's content_generation.VoiceProfile.
    """

    SENTENCE_LENGTH_CHOICES = [
        ("short", "Short & punchy"),
        ("medium", "Medium"),
        ("long", "Long & flowing"),
        ("varied", "Varied"),
    ]

    summary = models.TextField(blank=True, default="", help_text="One or two sentence summary of the voice")
    tone_words = models.JSONField(default=list, blank=True, help_text="List of tone/adjective words")
    sentence_length = models.CharField(max_length=10, choices=SENTENCE_LENGTH_CHOICES, default="varied")
    words_to_avoid = models.JSONField(default=list, blank=True, help_text="Words/phrases this voice never uses")
    sample_paragraphs = models.JSONField(default=list, blank=True, help_text="2-3 distilled sample paragraphs")
    do_notes = models.JSONField(default=list, blank=True, help_text="Do's for writing in this voice")
    dont_notes = models.JSONField(default=list, blank=True, help_text="Don'ts for writing in this voice")
    raw_response = models.TextField(blank=True, default="", help_text="Raw JSON returned by the model")
    enabled = models.BooleanField(default=True, help_text="Apply this voice to generated content")
    distilled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Voice profile"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def is_distilled(self):
        return self.distilled_at is not None

    def mark_distilled(self):
        self.distilled_at = timezone.now()


class ContentTemplate(models.Model):
    """A named recipe (e.g. 'Instagram carousel') — an ordered set of prompts
    that produce values for a ContentItem's fields in one run.
    Adapted from ai-marketing's content_templates.Template.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content_type = models.CharField(
        max_length=20, choices=ContentItem.CONTENT_TYPE_CHOICES, blank=True,
        help_text="Sets the generated item's content type",
    )
    default_platforms = models.ManyToManyField(
        Platform, blank=True, related_name="content_templates",
        help_text="Platforms pre-set on items generated from this template",
    )
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords to steer generation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ContentTemplatePrompt(models.Model):
    """One ordered step of a ContentTemplate, producing one ContentItem field.
    Adapted from ai-marketing's content_templates.TemplatePrompt.
    """

    # Must match attribute names on ContentItem so results map straight across.
    TARGET_FIELD_CHOICES = [
        ("topic", "Topic"),
        ("hook", "Hook"),
        ("caption", "Caption"),
        ("call_to_action", "Call to action"),
        ("hashtags", "Hashtags"),
    ]

    template = models.ForeignKey(ContentTemplate, on_delete=models.CASCADE, related_name="prompts")
    name = models.CharField(max_length=255)
    target_field = models.CharField(max_length=20, choices=TARGET_FIELD_CHOICES, default="caption")
    prompt = models.TextField(help_text="Instruction for this step, e.g. 'Write a scroll-stopping hook.'")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.template.name} · {self.name}"
