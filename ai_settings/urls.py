# ai_settings/urls.py
from django.urls import path

from . import views

app_name = "ai_settings"

urlpatterns = [
    path("", views.AISettingsView.as_view(), name="settings"),
    path("test/", views.AITestConnectionView.as_view(), name="test_connection"),
]
