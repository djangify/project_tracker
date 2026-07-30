# content_calendar/forms.py
from django import forms

from projects.models import Project

from .models import ContentItem, ContentTemplate

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


class GenerateForm(forms.Form):
    """The one-shot 'Generate' panel: pick a template or write a brief, pick a
    date, and produce a draft ContentItem."""

    template = forms.ModelChoiceField(
        queryset=ContentTemplate.objects.all(), required=False,
        empty_label="— None (use the brief) —",
        widget=forms.Select(attrs={"class": _SELECT}),
    )
    brief = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": _INPUT,
                                     "placeholder": "e.g. A post about summer skincare for busy parents"}),
        help_text="Required if no template is chosen. Also used as extra steering for a template.",
    )
    content_type = forms.ChoiceField(
        choices=[("", "—")] + ContentItem.CONTENT_TYPE_CHOICES, required=False,
        widget=forms.Select(attrs={"class": _SELECT}),
    )
    scheduled_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": _INPUT}, format="%Y-%m-%d"),
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(), required=False, empty_label="— No project —",
        widget=forms.Select(attrs={"class": _SELECT}),
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("template") and not cleaned.get("brief", "").strip():
            raise forms.ValidationError("Choose a template or write a brief (or both).")
        return cleaned


class VoiceProfileForm(forms.Form):
    """Paste writing samples to distill into the voice profile."""

    sample_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 12, "class": _INPUT,
                                     "placeholder": "Paste a few paragraphs of your own writing…"}),
        help_text="A few hundred words works best.",
    )
