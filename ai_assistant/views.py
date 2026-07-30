# ai_assistant/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import View

from ai_settings import ai_client

from . import agent

SESSION_KEY = "assistant_messages"


def _get_messages(request):
    return request.session.get(SESSION_KEY, [])


def _save_messages(request, messages):
    request.session[SESSION_KEY] = messages
    request.session.modified = True


def _render_messages(request, error=""):
    return render(request, "ai_assistant/_messages.html", {
        "messages": agent.display_messages(_get_messages(request)),
        "error": error,
    })


class ChatView(LoginRequiredMixin, View):
    template_name = "ai_assistant/chat.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "messages": agent.display_messages(_get_messages(request)),
        })


class ChatSendView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        text = (request.POST.get("message") or "").strip()
        if not text:
            return _render_messages(request)

        messages = _get_messages(request)
        messages.append({"role": "user", "content": text})

        error = ""
        try:
            _reply, messages = agent.run_turn(messages)
        except ai_client.AIConfigError as exc:
            error = f"{exc} Set one up in AI Settings."
        except Exception as exc:  # noqa: BLE001 — surface to the user, keep the app up
            error = f"Something went wrong: {type(exc).__name__}: {exc}"

        _save_messages(request, messages)
        return _render_messages(request, error=error)


class ChatClearView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        request.session[SESSION_KEY] = []
        request.session.modified = True
        return redirect(reverse("ai_assistant:chat"))
