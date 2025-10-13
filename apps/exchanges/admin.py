from django.contrib import admin

from .models import ExchangeAccount


@admin.register(ExchangeAccount)
class ExchangeAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "exchange_id",
        "owner",
        "enabled",
        "is_testnet",
        "created_at",
    )
    list_filter = ("exchange_id", "enabled", "is_testnet")
    search_fields = ("name", "owner__username", "exchange_id")
