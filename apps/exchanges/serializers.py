from rest_framework import serializers

from .models import ExchangeAccount


class ExchangeAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeAccount
        fields = [
            "id",
            "owner",
            "name",
            "exchange_id",
            "api_key",
            "api_secret",
            "password",
            "is_testnet",
            "enabled",
            "rate_limit_per_minute",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "owner", "created_at", "updated_at")
        extra_kwargs = {
            "api_key": {"write_only": True},
            "api_secret": {"write_only": True},
            "password": {"write_only": True},
        }
