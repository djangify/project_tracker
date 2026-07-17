# assets/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from pages.models import Page

from .models import Asset, GenerationJob, PromptTemplate, VoiceProfile
from .services import GenerationError, distill_voice_profile, generate_content

ASSET_FIELDS = ["title", "file", "file_type", "content", "tags", "project", "contact"]


def _text_to_editorjs_blocks(text):
    """Turn a plain-text AI response into Editor.js paragraph blocks, split on
    blank lines so it's readable/editable rather than one giant block."""
    blocks = []
    for chunk in text.split("\n\n"):
        chunk = chunk.strip()
        if chunk:
            blocks.append({"type": "paragraph", "data": {"text": chunk.replace("\n", "<br>")}})
    return {"blocks": blocks or [{"type": "paragraph", "data": {"text": text}}]}


class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"

    def get_queryset(self):
        qs = Asset.objects.all()
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(title__icontains=search)
        return qs


class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["prompt_templates"] = PromptTemplate.objects.filter(is_active=True)
        ctx["voice_profiles"] = VoiceProfile.objects.all()
        ctx["recent_jobs"] = self.object.generation_jobs.all()[:5]
        return ctx


class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    fields = ASSET_FIELDS
    template_name = "assets/asset_form.html"

    def get_success_url(self):
        return reverse("assets:detail", kwargs={"pk": self.object.pk})


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    fields = ASSET_FIELDS
    template_name = "assets/asset_form.html"

    def get_success_url(self):
        return reverse("assets:detail", kwargs={"pk": self.object.pk})


class AssetDeleteView(LoginRequiredMixin, DeleteView):
    model = Asset
    template_name = "assets/asset_confirm_delete.html"
    success_url = reverse_lazy("assets:list")


class GenerateView(LoginRequiredMixin, View):
    """Pick one or more assets, a prompt template and optional voice profile,
    and run generation synchronously. Saves the result as a new pages.Page."""

    def post(self, request, *args, **kwargs):
        asset_ids = request.POST.getlist("assets")
        template_id = request.POST.get("prompt_template")
        voice_id = request.POST.get("voice_profile")
        instructions = request.POST.get("instructions", "")
        fallback_url = request.META.get("HTTP_REFERER") or reverse("assets:list")

        if not asset_ids or not template_id:
            messages.error(request, "Pick at least one asset and a prompt template.")
            return redirect(fallback_url)

        job = GenerationJob.objects.create(
            prompt_template_id=template_id,
            voice_profile_id=voice_id or None,
            instructions=instructions,
            status="in_progress",
        )
        job.assets.set(asset_ids)

        try:
            text = generate_content(job)
        except GenerationError as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.save(update_fields=["status", "error_message"])
            messages.error(request, str(exc))
            return redirect(fallback_url)
        except Exception as exc:  # network/API errors etc. — don't 500 on a failed AI call
            job.status = "failed"
            job.error_message = str(exc)
            job.save(update_fields=["status", "error_message"])
            messages.error(request, f"Generation failed: {exc}")
            return redirect(fallback_url)

        page = Page.objects.create(
            title=job.prompt_template.name if job.prompt_template else "Generated content",
            content=_text_to_editorjs_blocks(text),
        )
        job.result_page = page
        job.status = "completed"
        job.completed_at = timezone.now()
        job.save(update_fields=["result_page", "status", "completed_at"])

        messages.success(request, "Content generated.")
        return redirect(page.get_absolute_url())


class VoiceProfileListView(LoginRequiredMixin, ListView):
    model = VoiceProfile
    template_name = "assets/voiceprofile_list.html"
    context_object_name = "voice_profiles"


class VoiceProfileCreateView(LoginRequiredMixin, CreateView):
    model = VoiceProfile
    fields = ["name", "source_assets", "is_active"]
    template_name = "assets/voiceprofile_form.html"

    def get_success_url(self):
        return reverse("assets:voice_detail", kwargs={"pk": self.object.pk})


class VoiceProfileDetailView(LoginRequiredMixin, DetailView):
    model = VoiceProfile
    template_name = "assets/voiceprofile_detail.html"
    context_object_name = "voice_profile"


class VoiceProfileDistillView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        voice_profile = get_object_or_404(VoiceProfile, pk=kwargs["pk"])
        try:
            distill_voice_profile(voice_profile)
            messages.success(request, "Voice profile updated from source assets.")
        except GenerationError as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f"Distillation failed: {exc}")
        return redirect("assets:voice_detail", pk=voice_profile.pk)
