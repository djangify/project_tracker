# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Add this function
def redirect_to_admin_login(request):
    return redirect('/admin/login/?next=' + request.GET.get('next', '/'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('projects/', include('projects.urls')),
    # login redirection
    path('accounts/login/', redirect_to_admin_login, name='login'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)