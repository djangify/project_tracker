# crm/models.py
from django.db import models
from django.utils import timezone


class Contact(models.Model):
    PLATFORM_CHOICES = [
        ("instagram", "Instagram"),
        ("linkedin", "LinkedIn"),
        ("x", "X / Twitter"),
        ("facebook", "Facebook"),
        ("tiktok", "TikTok"),
        ("youtube", "YouTube"),
        ("threads", "Threads"),
        ("reddit", "Reddit"),
        ("email", "Email"),
        ("referral", "Referral"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("replied", "Replied"),
        ("in_conversation", "In conversation"),
        ("converted", "Converted"),
        ("dead", "Dead / No interest"),
    ]

    name = models.CharField(max_length=150)
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default="instagram",
        help_text="Where you found them",
    )
    social_handle = models.CharField(
        max_length=150, blank=True, help_text="Their @username on that platform"
    )
    profile_url = models.URLField(blank=True, help_text="Link to their profile")
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    tags = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated, e.g. coach, warm lead"
    )
    notes = models.TextField(blank=True)

    follow_up_date = models.DateField(
        null=True, blank=True, help_text="When to follow up next"
    )
    follow_up_1_done = models.BooleanField("Follow-up 1 done", default=False)
    follow_up_2_done = models.BooleanField("Follow-up 2 done", default=False)
    follow_up_3_done = models.BooleanField("Follow-up 3 done", default=False)

    joined_live_it_list = models.BooleanField(
        default=False, help_text="Signed up for the free Live It List"
    )
    made_purchase = models.BooleanField(
        default=False, help_text="This contact has bought something"
    )
    revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount this contact has paid",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def follow_ups_complete(self):
        return self.follow_up_1_done and self.follow_up_2_done and self.follow_up_3_done

    @property
    def current_stage(self):
        """Next incomplete follow-up stage (1, 2 or 3), or None if all done."""
        if not self.follow_up_1_done:
            return 1
        if not self.follow_up_2_done:
            return 2
        if not self.follow_up_3_done:
            return 3
        return None

    @property
    def follow_up_overdue(self):
        if self.follow_up_date and not self.follow_ups_complete:
            return self.follow_up_date < timezone.localdate()
        return False

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class FollowUpTemplate(models.Model):
    STAGE_CHOICES = [(1, "Follow-up 1"), (2, "Follow-up 2"), (3, "Follow-up 3")]

    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES, unique=True)
    message = models.TextField(help_text="Reusable message for this follow-up stage")

    class Meta:
        ordering = ["stage"]

    def __str__(self):
        return self.get_stage_display()


class Interaction(models.Model):
    CHANNEL_CHOICES = [
        ("dm", "Direct message"),
        ("comment", "Comment"),
        ("email", "Email"),
        ("call", "Call"),
        ("meeting", "Meeting"),
        ("other", "Other"),
    ]

    DIRECTION_CHOICES = [
        ("outbound", "I reached out"),
        ("inbound", "They reached out"),
    ]

    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="interactions"
    )
    date = models.DateField(default=timezone.localdate)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="dm")
    direction = models.CharField(
        max_length=20, choices=DIRECTION_CHOICES, default="outbound"
    )
    message = models.TextField(help_text="What was said")
    image = models.ImageField(
        upload_to="crm/interactions/",
        blank=True,
        null=True,
        help_text="Optional screenshot (e.g. of a comment or DM)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_direction_display()} – {self.contact.name} ({self.date})"
