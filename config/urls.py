# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.static import serve


def redirect_to_admin_login(request):
    return redirect('/admin/login/?next=' + request.GET.get('next', '/'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('projects/', include('projects.urls')),
    # login redirection
    path('accounts/login/', redirect_to_admin_login, name='login'),
    path('static/<path:path>', serve, {
        'document_root': settings.STATIC_ROOT,
    }),
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
