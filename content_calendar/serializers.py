# content_calendar/serializers.py
from rest_framework import serializers

from .models import ContentItem, Platform


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ["id", "name", "order"]


class ContentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = [
            "id", "project", "scheduled_date", "pillar", "content_type", "topic",
            "platforms", "hook", "caption", "call_to_action", "hashtags",
            "tags_links", "audio_sound", "image_video_cover", "content_link",
            "status", "approval_status", "created_at", "updated_at", "order",
        ]
