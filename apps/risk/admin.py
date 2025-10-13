from django.contrib import admin

from .models import RiskProfile


@admin.register(RiskProfile)
class RiskProfileAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "max_concurrent_positions",
        "max_capital_per_position_pct",
        "daily_loss_limit_pct",
        "max_total_drawdown_pct",
        "updated_at",
    )
    search_fields = ("owner__username", "owner__email")
