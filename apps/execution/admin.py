from django.contrib import admin

from .models import Bot


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "strategy",
        "exchange_account",
        "status",
        "base_currency",
        "created_at",
    )
    list_filter = ("status", "base_currency")
    search_fields = ("name", "strategy__name", "exchange_account__name")
