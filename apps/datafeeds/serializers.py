from rest_framework import serializers

from .models import Candle, Symbol


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = [
            "id",
            "code",
            "ccxt_symbol",
            "base_asset",
            "quote_asset",
            "exchange",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")


class CandleSerializer(serializers.ModelSerializer):
    symbol = SymbolSerializer(read_only=True)

    class Meta:
        model = Candle
        fields = [
            "id",
            "symbol",
            "timeframe",
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "source",
        ]
        read_only_fields = fields
