# content_calendar/models.py
from django.db import models

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
        from django.utils import timezone

        return (
            self.scheduled_date is not None
            and self.status not in ("published", "archived")
            and self.scheduled_date < timezone.localdate()
        )
