# crm/serializers.py
from rest_framework import serializers
from .models import Contact, Interaction


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = [
            "id",
            "contact",
            "date",
            "channel",
            "direction",
            "message",
            "image",
            "created_at",
        ]


class ContactSerializer(serializers.ModelSerializer):
    interactions = InteractionSerializer(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "platform",
            "social_handle",
            "profile_url",
            "email",
            "status",
            "tags",
            "notes",
            "follow_up_date",
            "follow_up_1_done",
            "follow_up_2_done",
            "follow_up_3_done",
            "joined_live_it_list",
            "made_purchase",
            "revenue",
            "created_at",
            "updated_at",
            "interactions",
        ]
