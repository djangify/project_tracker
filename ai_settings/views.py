# ai_settings/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from . import ai_client
from .models import AIProviderConfig


def _ensure_rows():
    """Make sure there's a config row for each provider so the page can render
    all three regardless of what's been set up yet."""
    for provider, _label in AIProviderConfig.PROVIDER_CHOICES:
        AIProviderConfig.objects.get_or_create(provider=provider)


class AISettingsView(LoginRequiredMixin, TemplateView):
    template_name = "ai_settings/settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        _ensure_rows()
        configs = list(AIProviderConfig.objects.all())
        ctx["configs"] = configs
        ctx["active_provider"] = next(
            (c.provider for c in configs if c.is_active), ""
        )
        ctx["saved"] = self.request.GET.get("saved") == "1"
        return ctx

    def post(self, request, *args, **kwargs):
        _ensure_rows()
        active = request.POST.get("active_provider", "")
        for config in AIProviderConfig.objects.all():
            config.model_name = request.POST.get(f"model_name_{config.provider}", "").strip()
            # Only overwrite the key when a new value is typed; blank leaves it.
            new_key = request.POST.get(f"api_key_{config.provider}", "").strip()
            if new_key:
                config.api_key = new_key
            config.is_active = config.provider == active
            config.save()
        return redirect(reverse("ai_settings:settings") + "?saved=1")


class AITestConnectionView(LoginRequiredMixin, View):
    """Call the active provider with a trivial prompt and return its reply."""

    def post(self, request, *args, **kwargs):
        try:
            reply = ai_client.generate(
                system_prompt="You are a helpful assistant. Answer briefly.",
                user_prompt="Reply with a short friendly hello and name the AI model you are.",
                temperature=0.3,
            )
            return JsonResponse({"ok": True, "reply": reply})
        except ai_client.AIConfigError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001 — surface any SDK/network error to the user
            return JsonResponse({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, status=502)
