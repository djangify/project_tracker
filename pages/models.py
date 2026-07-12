# pages/models.py
from django.db import models
from django.urls import reverse


class Page(models.Model):
    """
    A Notion-style page. Pages nest infinitely via a self-referential parent
    and store their body as one Editor.js JSON document (see NOTION_UPGRADE_PLAN.md
    Phase 1 for the design rationale).
    """

    title = models.CharField(max_length=255, default="Untitled")
    icon = models.CharField(max_length=8, blank=True, help_text="Single emoji")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    content = models.JSONField(default=dict, blank=True)  # Editor.js output

    # Optional links into existing apps (used by Phase 3)
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pages",
    )
    contact = models.ForeignKey(
        "crm.Contact",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pages",
    )

    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)  # trash, not hard delete
    position = models.PositiveIntegerField(default=0)  # sibling ordering
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.icon} {self.title}".strip()

    def get_absolute_url(self):
        return reverse("pages:detail", kwargs={"pk": self.pk})

    def ancestors(self):
        """Return this page's ancestors, root first (for breadcrumbs)."""
        chain = []
        node = self.parent
        while node is not None:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def visible_children(self):
        """Non-archived direct children, ordered (for the sidebar tree)."""
        return self.children.filter(is_archived=False)
