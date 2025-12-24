from rest_framework import serializers

from .models import Candle, Symbol, Divergence


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


class DivergenceSerializer(serializers.ModelSerializer):
    symbol = SymbolSerializer(read_only=True)

    class Meta:
        model = Divergence
        fields = [
            "id",
            "symbol",
            "timeframe",
            "divergence_type",
            "start_timestamp",
            "start_price",
            "start_indicator_value",
            "end_timestamp",
            "end_price",
            "end_indicator_value",
            "is_bullish",
            "is_macd",
        ]
        read_only_fields = fields
