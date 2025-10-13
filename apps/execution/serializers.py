from rest_framework import serializers

from .models import Bot


class BotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bot
        fields = [
            "id",
            "name",
            "strategy",
            "exchange_account",
            "base_currency",
            "quote_universe",
            "starting_capital",
            "status",
            "last_heartbeat_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "status", "last_heartbeat_at", "created_at", "updated_at")
