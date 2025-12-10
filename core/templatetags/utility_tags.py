# core/templatetags/utility_tags.py
from django import template
from core.utils import format_duration, get_status_color

register = template.Library()

@register.filter
def minutes_to_time(minutes):
    """Template filter to format minutes as a human-readable duration"""
    return format_duration(minutes)


@register.filter
def status_bg_color(status):
    """Template filter to get background color class for a status"""
    return get_status_color(status)['bg']


@register.filter
def status_text_color(status):
    """Template filter to get text color class for a status"""
    return get_status_color(status)['text']
