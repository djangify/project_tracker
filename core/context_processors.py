# core/context_processors.py
from .utils import get_site_config

def site_config(request):
    """
    Context processor to add site configuration to all templates
    """
    return {
        'site_config': get_site_config(),
    }
