from django.contrib import admin

from .models import Strategy


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "owner", "is_live", "updated_at")
    search_fields = ("name", "slug", "owner__username")
    list_filter = ("is_live",)
    prepopulated_fields = {"slug": ("name",)}
