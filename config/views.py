# config/views.py
from django.http import JsonResponse


def health_check(request):
    """
    Health check endpoint.

    Used by the desktop app's startup probe (desktop.py waits for this to
    respond before opening the app window) and can double as an uptime check
    for the hosted deployment.
    """
    return JsonResponse({"status": "healthy"}, status=200)
