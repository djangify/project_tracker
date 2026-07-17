# assets/urls.py
from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("", views.AssetListView.as_view(), name="list"),
    path("create/", views.AssetCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AssetDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.AssetUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.AssetDeleteView.as_view(), name="delete"),
    path("generate/", views.GenerateView.as_view(), name="generate"),
    path("voices/", views.VoiceProfileListView.as_view(), name="voice_list"),
    path("voices/create/", views.VoiceProfileCreateView.as_view(), name="voice_create"),
    path("voices/<int:pk>/", views.VoiceProfileDetailView.as_view(), name="voice_detail"),
    path("voices/<int:pk>/distill/", views.VoiceProfileDistillView.as_view(), name="voice_distill"),
]
