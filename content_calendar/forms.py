# content_calendar/forms.py
from django import forms

from .models import ContentItem

_INPUT = (
    "mt-1 block w-full border border-gray-300 rounded-md py-2 px-3 "
    "focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
)
_SELECT = "bg-white " + _INPUT


class ContentItemForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = [
            "project", "scheduled_date", "pillar", "content_type", "topic",
            "platforms", "hook", "caption", "call_to_action", "hashtags",
            "tags_links", "audio_sound", "image_video_cover", "content_link",
            "status", "approval_status",
        ]
        widgets = {
            "scheduled_date": forms.DateInput(
                attrs={"type": "date", "class": _INPUT}, format="%Y-%m-%d"
            ),
            "hook": forms.Textarea(attrs={"rows": 2, "class": _INPUT}),
            "caption": forms.Textarea(attrs={"rows": 4, "class": _INPUT}),
            "hashtags": forms.Textarea(attrs={"rows": 2, "class": _INPUT}),
            "tags_links": forms.Textarea(attrs={"rows": 2, "class": _INPUT}),
            "platforms": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The date widget needs the format set so an existing value repopulates.
        self.fields["scheduled_date"].input_formats = ["%Y-%m-%d"]
        # Apply consistent styling to any field that didn't get a custom widget.
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue
            css = _SELECT if isinstance(widget, forms.Select) else _INPUT
            existing = widget.attrs.get("class", "")
            if "border" not in existing:  # don't double-apply to custom widgets
                widget.attrs["class"] = (existing + " " + css).strip()
