# crm/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "crm"

router = DefaultRouter()
router.register(r"contacts", views.ContactViewSet)
router.register(r"interactions", views.InteractionViewSet)

urlpatterns = [
    # Frontend URLs
    path("", views.ContactListView.as_view(), name="contact_list"),
    path("create/", views.ContactCreateView.as_view(), name="contact_create"),
    path("follow-ups/", views.FollowUpListView.as_view(), name="followups"),
    path("contact/<int:pk>/", views.ContactDetailView.as_view(), name="contact_detail"),
    path("contact/<int:pk>/edit/", views.ContactUpdateView.as_view(), name="contact_edit"),
    path(
        "contact/<int:contact_pk>/add-interaction/",
        views.InteractionCreateView.as_view(),
        name="interaction_create",
    ),
    path(
        "contact/<int:pk>/stage/<int:stage>/toggle/",
        views.StageToggleView.as_view(),
        name="stage_toggle",
    ),
    # API URLs
    path("api/", include(router.urls)),
]
