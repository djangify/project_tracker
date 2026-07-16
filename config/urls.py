# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.static import serve
from django.views.generic import TemplateView

# Customize admin site
admin.site.site_header = "Project Tracker"
admin.site.site_title = "Project Tracker Admin Portal"
admin.site.index_title = "Welcome to Project Tracker"


def redirect_to_admin_login(request):
    return redirect("/admin/login/?next=" + request.GET.get("next", "/"))


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("projects/", include("projects.urls")),
    path("crm/", include("crm.urls")),
    path("pages/", include("pages.urls")),
    # login redirection
    path("accounts/login/", redirect_to_admin_login, name="login"),
    path(
        "media/<path:path>",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
    # PWA: served at the site root (not under /static/) so the service
    # worker's scope covers the whole app.
    path(
        "manifest.json",
        TemplateView.as_view(template_name="manifest.json", content_type="application/manifest+json"),
        name="pwa_manifest",
    ),
    path(
        "sw.js",
        TemplateView.as_view(template_name="sw.js", content_type="application/javascript"),
        name="pwa_service_worker",
    ),
]
