# content_calendar/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "content_calendar"

router = DefaultRouter()
router.register(r"content", views.ContentItemViewSet)
router.register(r"platforms", views.PlatformViewSet)

urlpatterns = [
    # Content views (Table / Board / Calendar)
    path("", views.ContentCalendarView.as_view(), name="content_calendar"),
    path("table/", views.ContentTableView.as_view(), name="content_table"),
    path("board/", views.ContentBoardView.as_view(), name="content_board"),
    path("calendar/", views.ContentCalendarView.as_view(), name="content_calendar_alias"),
    path("new/", views.ContentItemCreateView.as_view(), name="content_create"),
    path("<int:pk>/edit/", views.ContentItemUpdateView.as_view(), name="content_edit"),
    path("<int:pk>/delete/", views.ContentItemDeleteView.as_view(), name="content_delete"),
    path("<int:pk>/set-approval/", views.ContentItemSetApprovalView.as_view(), name="content_set_approval"),

    # API URLs
    path("api/", include(router.urls)),
]
