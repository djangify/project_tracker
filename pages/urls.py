# pages/urls.py
from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("new/", views.PageCreateView.as_view(), name="create"),
    path("trash/", views.TrashView.as_view(), name="trash"),
    path("<int:pk>/", views.PageDetailView.as_view(), name="detail"),
    path("<int:pk>/content/", views.PageContentUpdateView.as_view(), name="content"),
    path("<int:pk>/favorite/", views.PageFavoriteToggleView.as_view(), name="favorite"),
    path("<int:pk>/archive/", views.PageArchiveView.as_view(), name="archive"),
    path("<int:pk>/restore/", views.PageRestoreView.as_view(), name="restore"),
    path("<int:pk>/delete/", views.PageDeleteView.as_view(), name="delete"),
]
