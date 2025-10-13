from rest_framework import serializers

from .models import Strategy


class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = [
            "id",
            "owner",
            "name",
            "slug",
            "description",
            "version",
            "config",
            "is_live",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "slug", "created_at", "updated_at", "owner")
