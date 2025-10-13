from django.contrib import admin

from .models import Candle, Symbol


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ("code", "exchange", "base_asset", "quote_asset", "is_active")
    search_fields = ("code", "base_asset", "quote_asset", "exchange")
    list_filter = ("exchange", "is_active")


@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):
    list_display = ("symbol", "timeframe", "timestamp", "open", "close", "volume")
    list_filter = ("timeframe", "symbol__exchange")
    search_fields = ("symbol__code",)
    ordering = ("-timestamp",)
    raw_id_fields = ("symbol",)
