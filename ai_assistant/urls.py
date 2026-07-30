# ai_assistant/urls.py
from django.urls import path

from . import views

app_name = "ai_assistant"

urlpatterns = [
    path("", views.ChatView.as_view(), name="chat"),
    path("send/", views.ChatSendView.as_view(), name="send"),
    path("clear/", views.ChatClearView.as_view(), name="clear"),
]
