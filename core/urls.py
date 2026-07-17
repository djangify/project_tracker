# core/urls.py
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('', views.DashboardView.as_view(), name='home'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
